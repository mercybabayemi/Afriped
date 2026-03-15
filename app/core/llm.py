"""LLM loader: Phi-3-mini-4k-instruct (primary) and TinyLlama-1.1B (judge).

Pipelines are globally cached via lru_cache — models load once per process,
never reloaded per request. 4-bit BnB quantization is used only when a GPU
is detected; CPU runs bfloat16 (halves RAM vs float32, avoids 16 Gi OOM).
"""
from __future__ import annotations

import torch
from functools import lru_cache
from typing import Optional

from loguru import logger
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline,
)

from app.core.config import settings


# ── BitsAndBytes 4-bit config (GPU only) ──────────────────────────────────────

def _bnb_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )


# ── Generic pipeline loader ────────────────────────────────────────────────────

def _load_pipeline(
    model_id: str,
    *,
    max_new_tokens: int = 512,
    use_quantization: bool = True,
) -> "pipeline":
    """Load a text-generation pipeline, cached globally by the callers.

    On CPU (free HF Space): runs float32, no quantization.
    On GPU: optionally applies 4-bit BnB quantization.
    """
    logger.info(f"Loading model: {model_id}")

    on_gpu = torch.cuda.is_available()
    device_map = "auto" if on_gpu else "cpu"
    quantization_config: Optional[BitsAndBytesConfig] = None

    if use_quantization and on_gpu:
        quantization_config = _bnb_config()
        logger.info("4-bit BnB quantization enabled")
    else:
        logger.info(
            "Running on CPU / quantization disabled — bfloat16, no BnB."
        )

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        token=settings.hf_token or None,
        trust_remote_code=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        token=settings.hf_token or None,
        quantization_config=quantization_config,
        device_map=device_map,
        torch_dtype=torch.bfloat16,  # bfloat16 on both GPU and CPU; halves RAM vs float32
        trust_remote_code=True,
    )
    model.eval()

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        repetition_penalty=1.1,
        return_full_text=False,
    )
    logger.info(f"Pipeline ready: {model_id}")
    return pipe


# ── Global singletons (loaded once, reused forever) ───────────────────────────

@lru_cache(maxsize=1)
def get_phi_pipeline():
    """Phi-3-mini-4k-instruct — primary content generation model."""
    return _load_pipeline(settings.main_model_id, max_new_tokens=512)


@lru_cache(maxsize=1)
def get_judge_pipeline():
    """TinyLlama 1.1B Chat — LLM-as-judge / validation model."""
    return _load_pipeline(settings.judge_model_id, max_new_tokens=256)


# ── Convenience wrapper ────────────────────────────────────────────────────────

def generate_text(
    messages: list[dict],
    *,
    use_judge: bool = False,
    max_new_tokens: int = 512,
) -> str:
    """Generate text using the appropriate cached pipeline.

    Args:
        messages: Chat-formatted list of dicts with ``role`` / ``content`` keys.
        use_judge: If True, use TinyLlama judge model; otherwise Phi-3-mini.
        max_new_tokens: Override default max new tokens.

    Returns:
        Generated text string.
    """
    pipe = get_judge_pipeline() if use_judge else get_phi_pipeline()

    # Clamp to CPU ceiling — prevents multi-minute waits on free Spaces
    if not torch.cuda.is_available():
        max_new_tokens = min(max_new_tokens, settings.cpu_max_tokens)

    result = pipe(
        messages,
        max_new_tokens=max_new_tokens,
        return_full_text=False,
    )

    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict):
            return first.get("generated_text", "")
        if isinstance(first, list) and first:
            return first[0].get("generated_text", "")

    logger.warning("Unexpected pipeline output format; returning empty string")
    return ""
