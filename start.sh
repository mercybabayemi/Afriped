#!/bin/bash
set -e

echo "=== AfriPed startup ==="
echo "BACKEND_URL: ${BACKEND_URL:-http://localhost:8000}"

# ── 1. Start FastAPI backend in background on port 8000 ───────────────────────
echo "[1/3] Starting FastAPI backend (port 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
FASTAPI_PID=$!

# ── 2. Wait for FastAPI health endpoint ───────────────────────────────────────
echo "[2/3] Waiting for FastAPI to be ready (model warmup takes 3-8 min on first run)..."
MAX_WAIT=600   # 10 minutes — first run downloads models
WAITED=0
until curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERROR: FastAPI did not become healthy in ${MAX_WAIT}s. Exiting."
        kill $FASTAPI_PID 2>/dev/null
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
done
echo "FastAPI ready after ${WAITED}s."

# ── 3. Start Gradio UI on port 7860 (foreground — keeps container alive) ──────
echo "[3/3] Starting Gradio UI (port 7860)..."
python app/ui/gradio_app.py
