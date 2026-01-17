# src/yonca/api/main.py
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from yonca.config import settings
from yonca.api.routes import health, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🌿 Yonca AI starting in {settings.deployment_mode.value} mode")
    print(f"🤖 LLM Provider: {settings.llm_provider.value}")
    print(f"📍 Running on http://{settings.api_host}:{settings.api_port}")
    yield
    # Shutdown
    print("🌿 Yonca AI shutting down")


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


# ===== Routes =====

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/yonca-ai", tags=["Chat"])


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
