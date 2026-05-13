# syntax=docker/dockerfile:1

# Multi-platform: linux/amd64, linux/arm64, linux/arm/v7 (armhf)
FROM python:3.11-slim

# Install system dependencies:
#   build-essential/gcc/libffi-dev - needed to build Python native extensions on multi-arch builds
#   ffmpeg  - required by pytapo Downloader for video assembly
#   libgomp1 - OpenMP runtime required by some numpy/ML deps on ARM
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    ffmpeg \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Static frontend is volume-mounted at runtime (see docker-compose.yml)
RUN mkdir -p /app/static /app/data/recordings /app/data/frames /app/data/db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
