"""Application configuration via pydantic-settings (reads from .env)."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    hf_token: str = ""
    main_model_id: str = "microsoft/Phi-3-mini-4k-instruct"
    judge_model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    embedding_model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./data/vectorstore"
    backend_url: str = "http://localhost:8000"
    max_tokens_default: int = 256
    cpu_max_tokens: int = 1024       # hard ceiling applied in generate_text on CPU
    rag_top_k_default: int = 4
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
