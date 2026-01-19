# src/yonca/api/main.py
"""FastAPI application entry point with multi-user scalability support."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from yonca.config import settings
from yonca.api.routes import health, chat, models
from yonca.api.middleware.rate_limit import RateLimitMiddleware, RateLimiter, RateLimitExceeded
from yonca.data.redis_client import RedisClient
from yonca.llm.http_pool import HTTPClientPool
from yonca.observability import (
    print_startup_banner,
    print_section_header,
    print_status_line,
    print_endpoints,
    print_quick_links,
    print_shutdown_message,
    print_startup_complete,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper resource management."""
    # ═══════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════
    
    # Main banner
    print_startup_banner("api", settings.app_version, "development")
    
    # LLM Configuration
    print_section_header("🤖 LLM Configuration")
    
    mode_display = "Open-Source" if settings.deployment_mode.value == "open_source" else "Proprietary Cloud"
    provider_display = "Groq" if settings.llm_provider.value == "groq" else "Gemini"
    
    print_status_line("Mode", mode_display, "info")
    print_status_line("Provider", provider_display, "success")
    print_status_line("Model", settings.active_llm_model, "success")
    
    if settings.llm_provider.value == "groq":
        print_status_line("Self-Host", "Ready (open-source models)", "info")
    
    # Infrastructure Status
    print_section_header("🔌 Infrastructure")
    
    # Redis connectivity
    redis_ok = False
    try:
        redis_ok = await RedisClient.health_check()
        if redis_ok:
            redis_host = settings.redis_url.replace("redis://", "").split("/")[0]
            print_status_line("Redis", "Connected", "success", f"{redis_host} (checkpointing)")
        else:
            print_status_line("Redis", "Not Available", "warning", "sessions will be stateless")
    except Exception as e:
        print_status_line("Redis", "Connection Failed", "error", str(e)[:40])
    
    # Rate limiting
    print_status_line("Rate Limit", f"{settings.rate_limit_requests_per_minute} req/min", "info", f"burst: {settings.rate_limit_burst}")
    
    # Endpoints with clickable links
    display_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    base_url = f"http://{display_host}:{settings.api_port}"
    
    print_endpoints([
        ("API", base_url, "REST API base"),
        ("Swagger", f"{base_url}/docs", "Interactive documentation"),
        ("ReDoc", f"{base_url}/redoc", "Alternative docs"),
        ("Health", f"{base_url}/health", "Service health check"),
    ])
    
    print_quick_links([
        ("Swagger", f"{base_url}/docs"),
        ("Chat API", f"{base_url}/api/v1/chat"),
        ("Models", f"{base_url}/api/models"),
    ])
    
    print_startup_complete("Yonca AI API")
    
    yield
    
    # ═══════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ═══════════════════════════════════════════════════════════════
    
    print_shutdown_message()
    
    # Close HTTP connection pools
    await HTTPClientPool.close_all()
    print_status_line("HTTP Pools", "Closed", "success")
    
    # Close Redis connections
    await RedisClient.close()
    print_status_line("Redis", "Closed", "success")
    
    print()
    print_status_line("Yonca AI", "Shutdown complete", "success")
    print()


app = FastAPI(
    title=settings.app_name,
    description="AI Farming Assistant for Azerbaijani Farmers",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ===== Error Handlers =====


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Bad Request",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):  # noqa: ARG001
    """Handle rate limit exceeded exceptions."""
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail)}
    retry_after = detail.get("retry_after", 60) if isinstance(detail, dict) else 60
    return JSONResponse(
        status_code=429,
        content=detail,
        headers={"Retry-After": str(retry_after)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    # Log the error in production
    if not settings.debug:
        # In production, don't expose internal error details
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
                "path": str(request.url),
            },
        )
    # In debug mode, expose the error details
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": str(request.url),
        },
    )


# ===== CORS Middleware =====

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Rate Limiting Middleware =====
# Applied after CORS so preflight requests aren't rate limited

app.add_middleware(
    RateLimitMiddleware,
    limiter=RateLimiter(
        requests_per_minute=settings.rate_limit_requests_per_minute,
        burst_limit=settings.rate_limit_burst,
    ),
)


# ===== Routes =====

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(models.router, prefix="/api", tags=["Models"])


# ===== Root Endpoint =====


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI Farming Assistant for Azerbaijani Farmers",
        "docs": "/docs",
        "health": "/health",
    }
