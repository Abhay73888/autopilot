# ==============================================================================
# AUTOPILOT - Autonomous AI YouTube Shorts Studio & Swarm Dashboard
# Optimized Dockerfile for Railway.app & Production Cloud Deployments
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HOST=0.0.0.0

# Install system dependencies: FFmpeg, TTF Fonts, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data and logs directories exist
RUN mkdir -p data logs output

# Expose ports (Render uses 10000 by default, local/dev 8000 or 8765)
EXPOSE 10000 8000 8765

# Start Autopilot Production SaaS Studio (binds dynamically to Render's $PORT, defaulting to 10000)
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-10000}"]
