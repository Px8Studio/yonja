# src/yonca/api/routes/health.py
"""Health check endpoints with scalability metrics."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from yonca.config import settings
from yonca.data.redis_client import RedisClient
from yonca.llm.http_pool import HTTPClientPool

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
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if the application is ready to serve traffic.
    Verifies LLM provider, Redis, and other critical services.
    """
    from yonca.llm.factory import check_llm_health

    # Check LLM provider health
    try:
        llm_health = await check_llm_health()
        llm_ready = llm_health.get("healthy", False)
    except Exception:
        llm_ready = False

    # Check Redis health
    try:
        redis_ready = await RedisClient.health_check()
    except Exception:
        redis_ready = False

    checks = {
        "config_loaded": True,
        "llm_provider": llm_ready,
        "redis": redis_ready,
    }

    # Core readiness requires LLM, Redis is optional (graceful degradation)
    core_ready = checks["config_loaded"] and checks["llm_provider"]

    return ReadinessResponse(
        ready=core_ready,
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


@router.get("/scalability")
async def scalability_status():
    """
    Scalability and resource status endpoint.

    Returns information about connection pools, rate limits,
    and multi-user capacity for monitoring.
    """
    # Redis connection status
    try:
        redis_healthy = await RedisClient.health_check()
    except Exception:
        redis_healthy = False

    # HTTP pool stats
    pool_stats = HTTPClientPool.get_pool_stats()

    return {
        "redis": {
            "healthy": redis_healthy,
            "url": settings.redis_url,
            "max_connections": settings.redis_max_connections,
        },
        "http_pools": pool_stats,
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": settings.rate_limit_requests_per_minute,
            "burst_limit": settings.rate_limit_burst,
        },
        "capacity": {
            "estimated_concurrent_users": min(
                settings.redis_max_connections,
                100,  # Conservative estimate based on connection pool
            ),
            "session_ttl_seconds": 3600,  # 1 hour default
        },
    }
