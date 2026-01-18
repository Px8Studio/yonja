# src/yonca/api/routes/health.py
"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from yonca.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    deployment_mode: str
    llm_provider: str
    llm_model: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic application health status and configuration.
    """
    return HealthResponse(
        status="healthy",
        deployment_mode=settings.deployment_mode.value,
        llm_provider=settings.llm_provider.value,
        llm_model=settings.active_llm_model,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if the application is ready to serve traffic.
    Can be extended to check database, redis, LLM provider connectivity.
    """
    from yonca.llm.factory import check_llm_health
    
    # Check LLM provider health
    try:
        llm_health = await check_llm_health()
        llm_ready = llm_health.get("healthy", False)
    except Exception:
        llm_ready = False
    
    checks = {
        "config_loaded": True,
        "llm_provider": llm_ready,
        # TODO: Add more checks as services are implemented
        # "database": await check_database_connection(),
        # "redis": await check_redis_connection(),
    }
    
    all_ready = all(checks.values())
    
    return ReadinessResponse(
        ready=all_ready,
        checks=checks,
    )


@router.get("/providers")
async def check_providers():
    """
    Check health of all configured LLM providers.
    
    Returns status for each provider (Ollama, Groq, Gemini).
    Useful for debugging and selecting the fastest available provider.
    """
    from yonca.llm.factory import check_all_providers_health
    
    return await check_all_providers_health()


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple endpoint to verify the application is running.
    Used by Kubernetes for liveness probes.
    """
    return {"alive": True}
