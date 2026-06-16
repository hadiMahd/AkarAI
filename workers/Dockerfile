FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV headless and lightgbm
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install shared + worker dependencies without pulling the full backend web stack
COPY backend/requirements.shared.txt /app/backend/requirements.shared.txt
COPY workers/requirements.txt /app/workers/requirements.txt
WORKDIR /app/workers
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy backend app modules (needed by worker handlers)
COPY backend/app /app/backend/app

# Copy worker code
COPY workers/ /app/workers/

WORKDIR /app/workers

CMD ["python", "main.py"]
