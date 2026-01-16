"""
Yonca AI - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from yonca.config import settings
from yonca.api.routes import router as api_router
from yonca.api.graphql import graphql_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"🌿 Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    print(f"🌿 Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-driven daily farm planning assistant for Yonca platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(api_router, prefix=settings.api_prefix)

# Include GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "message": "Xoş gəlmisiniz! Yonca AI hazırdır. 🌿"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
