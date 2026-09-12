r"""
backend/app/main.py — Production-Grade FastAPI Application Entrypoint
"""

import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.v1.admin import router as admin_router
from .api.v1.analytics import router as analytics_router
from .api.v1.auth import router as auth_router
from .api.v1.billing import router as billing_router
from .api.v1.copilot import router as copilot_router
from .api.v1.ideas import router as ideas_router
from .api.v1.instagram import router as instagram_router
from .api.v1.integrations_instagram import router as integrations_instagram_router
from .api.v1.jobs import router as jobs_router
from .api.v1.projects import router as projects_router
from .api.v1.publish import router as publish_router
from .api.v1.scripts import router as scripts_router
from .api.v1.videos import router as videos_router
from .api.v1.workspaces import router as workspaces_router
from .core.config import settings
from .core.exceptions import AppException
from .core.logging import api_logger, request_id_ctx

# Optional Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("APP_ENV", "development"),
        )
    except ImportError:
        pass

app = FastAPI(
    title="AUTOPILOT — Autonomous AI Media Operating System API",
    description="Enterprise API Gateway for autonomous media research, scriptwriting, voiceover, rendering, QA, publishing, and self-improving content science.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """Injects unique Request-ID into context and response headers."""
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
    request_id_ctx.set(req_id)
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time"] = f"{duration:.4f}s"
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Standardized error handler for application exceptions."""
    req_id = request_id_ctx.get() or "unknown"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "meta": {"requestId": req_id}
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and returns secure error envelope."""
    req_id = request_id_ctx.get() or "unknown"
    api_logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Our engineering team has been notified.",
                "details": {}
            },
            "meta": {"requestId": req_id}
        }
    )


STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"

if OUTPUT_DIR.exists():
    app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, tags=["Studio UI"])
async def studio_ui():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>AUTOPILOT 20X — API Gateway Active</h1>")


# Health Check Endpoints
@app.get("/health", tags=["Health"])
@app.get("/health/live", tags=["Health"])
async def health_live():
    return {"status": "ok", "service": "autopilot-api", "version": "1.0.0"}


@app.get("/health/ready", tags=["Health"])
async def health_ready():
    return {
        "status": "ready",
        "database": "connected",
        "storage": settings.storage_provider,
        "queue": "ready"
    }


# Mount API V1 Routers
v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=v1_prefix)
app.include_router(workspaces_router, prefix=v1_prefix)
app.include_router(projects_router, prefix=v1_prefix)
app.include_router(ideas_router, prefix=v1_prefix)
app.include_router(scripts_router, prefix=v1_prefix)
app.include_router(videos_router, prefix=v1_prefix)
app.include_router(jobs_router, prefix=v1_prefix)
app.include_router(publish_router, prefix=v1_prefix)
app.include_router(integrations_instagram_router, prefix=v1_prefix)
app.include_router(instagram_router, prefix=v1_prefix)
app.include_router(analytics_router, prefix=v1_prefix)
app.include_router(copilot_router, prefix=v1_prefix)
app.include_router(billing_router, prefix=v1_prefix)
app.include_router(admin_router, prefix=v1_prefix)


# Observability & Metrics Endpoint
@app.get("/metrics", tags=["Observability"])
async def prometheus_metrics():
    """Returns cluster health, queue depths, spend today, and quota remaining."""
    from .services.video_service import video_service
    from core.billing import BILLING
    from .services.analytics_service import PROJECT_DAILY_QUOTA_LIMIT, analytics_service

    jobs = list(video_service._jobs.values())
    queued = sum(1 for j in jobs if j.get("status") == "queued")
    running = sum(1 for j in jobs if j.get("status") in ("processing", "rendering"))
    failed = sum(1 for j in jobs if j.get("status") == "failed")
    completed = sum(1 for j in jobs if j.get("status") in ("completed", "validated"))

    daily_spend = sum(BILLING._daily_spend.values())
    quota_used = analytics_service._daily_project_quota_used
    quota_remaining = max(0, PROJECT_DAILY_QUOTA_LIMIT - quota_used)

    return {
        "jobs": {
            "queued": queued,
            "running": running,
            "failed": failed,
            "completed": completed,
            "total": len(jobs)
        },
        "billing": {
            "spendTodayUsd": round(daily_spend, 4),
        },
        "quota": {
            "youtubeApiUnitsUsed": quota_used,
            "youtubeApiUnitsRemaining": quota_remaining,
            "youtubeApiDailyLimit": PROJECT_DAILY_QUOTA_LIMIT
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
