FROM python:3.11-slim

# System dependencies for PyTorch, chromadb, and lingua-language-detector
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# HuggingFace model cache — keeps downloaded models in the image layer
# so warm restarts don't re-download 4GB of weights
ENV HF_HOME=/app/.hf_cache
RUN mkdir -p /app/.hf_cache

# Gradio calls FastAPI on port 8000 (internal — not exposed externally)
ENV BACKEND_URL=http://localhost:8000

# HuggingFace Spaces always routes external traffic to port 7860
EXPOSE 7860

RUN chmod +x start.sh

CMD ["bash", "start.sh"]
