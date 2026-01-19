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
    print_llm_info,
    print_database_info,
    print_infrastructure_summary,
    print_model_capabilities,
    print_security_info,
    print_observability_info,
    is_langfuse_healthy,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with proper resource management."""
    # ═══════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════
    
    # Main banner
    print_startup_banner("api", settings.app_version, settings.environment)
    
    # ─────────────────────────────────────────────────────────────
    # LLM Configuration (with detailed info)
    # ─────────────────────────────────────────────────────────────
    provider_names = {
        "groq": "Groq (LPU Cloud)",
        "ollama": "Ollama (Local)",
        "gemini": "Google Gemini",
    }
    provider_display = provider_names.get(settings.llm_provider.value, settings.llm_provider.value)
    
    # Determine mode and API key status
    mode = "local" if settings.llm_provider.value == "ollama" else "open_source" if settings.llm_provider.value == "groq" else "cloud"
    api_key_set = bool(
        (settings.llm_provider.value == "groq" and settings.groq_api_key) or
        (settings.llm_provider.value == "gemini" and settings.gemini_api_key) or
        settings.llm_provider.value == "ollama"
    )
    
    # Get base URL for the provider
    base_urls = {
        "ollama": settings.ollama_base_url,
        "groq": "https://api.groq.com/openai/v1",
        "gemini": "https://generativelanguage.googleapis.com",
    }
    
    print_llm_info(
        provider=provider_display,
        model=settings.active_llm_model,
        mode=mode,
        base_url=base_urls.get(settings.llm_provider.value),
        api_key_set=api_key_set,
    )
    
    # Show model-specific capabilities
    print_model_capabilities(settings.active_llm_model)
    
    # ─────────────────────────────────────────────────────────────
    # Infrastructure Status
    # ─────────────────────────────────────────────────────────────
    print_section_header("🔌 Infrastructure")
    
    # Redis connectivity
    redis_ok = False
    try:
        redis_ok = await RedisClient.health_check()
    except Exception:
        pass
    
    # Build services list
    services = []
    
    # Database info
    if "postgresql" in settings.database_url:
        try:
            db_host = settings.database_url.split("@")[-1].split("/")[0]
        except Exception:
            db_host = "configured"
        services.append({
            "name": "PostgreSQL",
            "status": "Connected",
            "style": "success",
            "port": db_host.split(":")[-1] if ":" in db_host else "5432",
            "detail": "user data & sessions",
        })
    
    # Redis
    if redis_ok:
        services.append({
            "name": "Redis",
            "status": "Connected",
            "style": "success",
            "port": "6379",
            "detail": "LangGraph checkpointing",
        })
    else:
        services.append({
            "name": "Redis",
            "status": "Not Available",
            "style": "warning",
            "detail": "sessions will be stateless",
        })
    
    # Ollama (if local mode)
    if settings.llm_provider.value == "ollama":
        services.append({
            "name": "Ollama",
            "status": "Configured",
            "style": "info",
            "port": "11434",
            "detail": f"model: {settings.ollama_model}",
        })
    
    for svc in services:
        port_info = f":{svc.get('port')}" if svc.get('port') else ""
        detail = svc.get('detail', '')
        if port_info and detail:
            full_detail = f"localhost{port_info} — {detail}"
        elif port_info:
            full_detail = f"localhost{port_info}"
        else:
            full_detail = detail
            
        print_status_line(svc['name'], svc['status'], svc.get('style', 'info'), full_detail)
    
    # ─────────────────────────────────────────────────────────────
    # Security Configuration
    # ─────────────────────────────────────────────────────────────
    jwt_configured = settings.jwt_secret != "dev-secret-change-in-production"
    print_security_info(
        rate_limit=settings.rate_limit_requests_per_minute,
        burst_limit=settings.rate_limit_burst,
        jwt_configured=jwt_configured,
        cors_origins=settings.cors_origins,
    )
    
    # ─────────────────────────────────────────────────────────────
    # Observability
    # ─────────────────────────────────────────────────────────────
    langfuse_ok = settings.langfuse_enabled and bool(settings.langfuse_secret_key)
    print_observability_info(
        langfuse_enabled=langfuse_ok,
        langfuse_url=settings.langfuse_host,
        prometheus_enabled=settings.prometheus_enabled,
        log_level=settings.log_level,
    )
    
    # ─────────────────────────────────────────────────────────────
    # Endpoints with clickable links
    # ─────────────────────────────────────────────────────────────
    display_host = "localhost" if settings.api_host == "0.0.0.0" else settings.api_host
    base_url = f"http://{display_host}:{settings.api_port}"
    
    print_endpoints([
        ("API", base_url, "REST API base"),
        ("Swagger", f"{base_url}/docs", "Interactive API documentation"),
        ("ReDoc", f"{base_url}/redoc", "Alternative API docs"),
        ("Health", f"{base_url}/health", "Readiness & liveness probes"),
    ])
    
    print_quick_links([
        ("Swagger", f"{base_url}/docs"),
        ("Chat", f"{base_url}/api/v1/chat"),
        ("Langfuse", settings.langfuse_host),
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
