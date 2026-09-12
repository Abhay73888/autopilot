# AUTOPILOT — CLOUD DEPLOYMENT & DEVOPS SPECIFICATION

This document details the production containerization, infrastructure provisioning, background worker topology, and CI/CD pipelines for AUTOPILOT.

---

## 1. PRODUCTION INFRASTRUCTURE TOPOLOGY

```text
               Global Creators / Web App
                          │
                          ▼
            Cloudflare (DNS + SSL + WAF + CDN)
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
    Frontend Web (Vercel)          API Gateway (Render/Railway)
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   ▼                      ▼                      ▼
           Supabase Postgres           Redis (Upstash)      Cloudflare R2
          (Data + Auth + RLS)        (Queue + PubSub)     (Object Storage)
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
     Standard Workers (CPU)                                      GPU Workers (Modal/RunPod)
     - TrendScout / ScriptWriter                                 - High-res SDXL / Flux
     - NeuralVoice (TTS)                                         - NVENC Hardware FFmpeg
     - MultiPublisher / Analytics
```

---

## 2. DOCKER ARCHITECTURE

### 2.1 Multi-Stage Production Dockerfile (`Dockerfile`)

```dockerfile
# ========================================================
# Stage 1: Base image with FFmpeg and audio dependencies
# ========================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system utilities and FFmpeg with full codec support
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    curl \
    ca-certificates \
    fonts-inter \
    && rm -rf /var/lib/apt/lists/*

# ========================================================
# Stage 2: Python dependencies builder
# ========================================================
FROM base AS builder

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# ========================================================
# Stage 3: Final Production Image
# ========================================================
FROM base AS runner

# Create non-root system user for security
RUN groupadd -r autopilot && useradd -r -g autopilot -s /bin/false autopilot

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

# Set permissions
RUN chown -R autopilot:autopilot /app

USER autopilot

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8765/api/v1/health || exit 1

CMD ["python", "-m", "web.server", "--host", "0.0.0.0", "--port", "8765"]
```

---

### 2.2 Docker Compose Production Specification (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  # 1. API Server
  api:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - STORAGE_ENDPOINT=${STORAGE_ENDPOINT}
      - STORAGE_ACCESS_KEY=${STORAGE_ACCESS_KEY}
      - STORAGE_SECRET_KEY=${STORAGE_SECRET_KEY}
    depends_on:
      redis:
        condition: service_healthy

  # 2. Redis Queue & Event Broker
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 3. Dedicated Background Rendering Worker
  worker_render:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    command: ["python", "-m", "workers.render_worker"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - STORAGE_ENDPOINT=${STORAGE_ENDPOINT}
      - STORAGE_ACCESS_KEY=${STORAGE_ACCESS_KEY}
      - STORAGE_SECRET_KEY=${STORAGE_SECRET_KEY}
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8192M

  # 4. Dedicated AI & Analytics Worker
  worker_agents:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    command: ["python", "-m", "workers.agent_worker"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

volumes:
  redis_data:
```

---

## 3. GPU WORKER PROVISIONING (MODAL / RUNPOD)

For heavy AI image/video synthesis and accelerated FFmpeg NVENC rendering, GPU tasks are offloaded to **Modal** serverless functions or a dedicated RunPod container.

### Example Modal Serverless GPU Renderer (`workers/modal_renderer.py`):
```python
import modal

app = modal.App("autopilot-gpu-renderer")

image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")
    .pip_install("torch", "diffusers", "transformers", "accelerate")
)

@app.function(image=image, gpu="A10G", timeout=300)
def render_video_with_gpu(job_payload: dict) -> dict:
    """
    Renders high-definition vertical video using hardware NVENC encoding
    and generates custom scene keyframes via SDXL.
    """
    # 1. Synthesize keyframes on A10G GPU
    # 2. Execute NVENC FFmpeg pipeline
    # 3. Upload directly to Cloudflare R2 bucket
    return {"status": "success", "video_url": "https://..."}
```

---

## 4. GITHUB ACTIONS CI/CD PIPELINE (`.github/workflows/deploy.yml`)

```yaml
name: Production CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test_and_lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest flake8 black

      - name: Lint and Format Check
        run: |
          black --check .
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run Unit & Regression Tests
        run: |
          pytest tests/

  deploy_production:
    needs: test_and_lint
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy API & Workers to Render / Railway
        env:
          DEPLOY_WEBHOOK: ${{ secrets.RENDER_DEPLOY_WEBHOOK }}
        run: |
          curl -X POST "$DEPLOY_WEBHOOK"
```

---

## 5. OBSERVABILITY, LOGGING & MONITORING

1. **Error Tracking**: Integrated **Sentry SDK** catches unhandled exceptions in both API handlers and asynchronous background workers with breadcrumbs and user context.
2. **Healthcheck Endpoint**: `GET /api/v1/health` checks:
   - PostgreSQL connection pool health (`SELECT 1`)
   - Redis ping latency
   - Local disk space and FFmpeg binary availability
3. **Structured Logging**: All logs formatted as JSON with fields:
   `{"timestamp": "...", "level": "INFO", "workspace_id": "...", "job_id": "...", "message": "..."}`
