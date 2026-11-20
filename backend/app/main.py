"""CareerPilot AI - FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.database import get_db, init_db
from app.api.routes import agent, analysis, health, history, interview, jobs, optimizer, resume

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("careerpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    provider = "gemini" if settings.gemini_api_key else "local bridge / rule-based"
    logger.info("%s v%s started (AI provider: %s)", settings.app_name, settings.app_version, provider)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered campus placement assistant: resume intelligence, job description "
        "analysis, explainable resume-job matching, skill gap plans, resume "
        "optimization and mock interviews.\n\n"
        "**Note**: match scores are explainable preparation estimates, not employer "
        "ATS scores."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def catch_errors(request: Request, call_next):
    """Global error safety net - never leak internals to the client."""
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": {"message": "An unexpected error occurred. Please try again.", "code": "internal_error"}},
        )


# Routers (all under /api).
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(resume.router, prefix=settings.api_prefix)
app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
app.include_router(history.router, prefix=settings.api_prefix)
app.include_router(optimizer.router, prefix=settings.api_prefix)
app.include_router(interview.router, prefix=settings.api_prefix)
app.include_router(agent.router, prefix=settings.api_prefix)


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
