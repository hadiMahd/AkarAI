FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV headless and lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies first (includes media processing libs)
COPY backend/requirements.txt /app/backend-requirements.txt
RUN pip install --no-cache-dir -r /app/backend-requirements.txt

# Install worker dependencies
COPY workers/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend app modules (needed by worker handlers)
COPY backend/app /app/backend/app

# Copy worker code
COPY workers/ /app/workers/

WORKDIR /app/workers

CMD ["python", "main.py"]
