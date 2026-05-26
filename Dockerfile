FROM python:3.11-slim

# System libs needed by lxml and (some) scientific wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HuggingFace model cache (mount a volume to persist across runs / go offline).
ENV HF_HOME=/app/.hf_cache

# Wait for Grobid (if configured) then run the full pipeline.
ENTRYPOINT ["sh", "-c", "python wait_for_grobid.py && python -m src.pipeline --config config/config.yaml"]
