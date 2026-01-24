import asyncio
import os
from typing import TypedDict

import httpx
from chainlit.data.chainlit_data_layer import ChainlitDataLayer
from config import settings as demo_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from services.logger import get_logger, setup_logging

# Initialize structured logging
setup_logging(level="INFO", json_format=True)
logger = get_logger(__name__)

# ============================================
# MCP STATUS MONITORING
# ============================================


class MCPServiceStatus(TypedDict):
    """Status of an MCP service."""

    name: str
    url: str
    status: str  # "online" | "offline" | "degraded"
    response_time_ms: float | None
    version: str | None


MCP_SERVICES = {
    "zekalab": {
        "name": "ZekaLab Internal Rules",
        "url": os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777"),
        "health_endpoint": "/health",
    },
    "langgraph": {
        "name": "LangGraph API",
        "url": demo_settings.langgraph_base_url,
        "health_endpoint": "/ok",
    },
}


async def check_mcp_health(service_key: str) -> MCPServiceStatus:
    """Check health of a single MCP service."""
    service = MCP_SERVICES.get(service_key)
    if not service:
        return MCPServiceStatus(
            name=service_key,
            url="unknown",
            status="offline",
            response_time_ms=None,
            version=None,
        )

    url = f"{service['url']}{service['health_endpoint']}"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            import time

            start = time.monotonic()
            response = await client.get(url)
            elapsed_ms = (time.monotonic() - start) * 1000

            if response.status_code == 200:
                data = (
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else {}
                )
                return MCPServiceStatus(
                    name=service["name"],
                    url=service["url"],
                    status="online",
                    response_time_ms=round(elapsed_ms, 1),
                    version=data.get("version"),
                )
            else:
                return MCPServiceStatus(
                    name=service["name"],
                    url=service["url"],
                    status="degraded",
                    response_time_ms=round(elapsed_ms, 1),
                    version=None,
                )
    except Exception:
        return MCPServiceStatus(
            name=service["name"],
            url=service["url"],
            status="offline",
            response_time_ms=None,
            version=None,
        )


async def get_all_mcp_status() -> dict[str, MCPServiceStatus]:
    """Check all MCP services in parallel."""
    tasks = {key: check_mcp_health(key) for key in MCP_SERVICES}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    return {
        key: (
            result
            if not isinstance(result, Exception)
            else MCPServiceStatus(
                name=MCP_SERVICES[key]["name"],
                url=MCP_SERVICES[key]["url"],
                status="offline",
                response_time_ms=None,
                version=None,
            )
        )
        for key, result in zip(tasks.keys(), results)
    }


async def init_chainlit_data_layer():
    """Initialize Chainlit's SQLAlchemy data layer with async engine.

    CRITICAL: This function now performs a BLOCKING connection test.
    If the database is unreachable, it will RAISE an error and HALT startup.
    """
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/yonca.db")
        logger.info(
            f"Initializing Chainlit data layer with: {db_url.split('@')[-1] if '@' in db_url else db_url}"
        )

        # Create async engine
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # STRICT STARTUP CHECK: Verify Database Connection
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("[OK] Database connection verified (SELECT 1 success)")
        except Exception as db_err:
            logger.critical(f"[ERROR] DATABASE CONNECTION FAILED: {db_err}")
            logger.critical("The application cannot start without the database.")
            raise RuntimeError(f"Database connection failed: {db_err}") from db_err

        # Create async session factory
        sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize PostgreSQL storage provider for file elements
        from storage_postgres import get_postgres_storage_client

        storage_provider = None
        if "postgresql" in db_url or "postgres" in db_url:
            try:
                storage_provider = get_postgres_storage_client(database_url=db_url)
                logger.info("[OK] PostgreSQL storage provider initialized for file elements")
            except Exception as storage_err:
                logger.error(f"[WARN] PostgreSQL storage provider failed: {storage_err}")
                logger.error("   File elements (images, docs) will not be persisted")

        # Initialize Chainlit data layer
        from data_layer import YoncaDataLayer

        data_layer = YoncaDataLayer(
            conninfo=db_url,
            storage_provider=storage_provider,
        )

        # Set as global data layer
        ChainlitDataLayer._instance = data_layer

        logger.info("[OK] Chainlit data layer initialized successfully")
        return data_layer
    except Exception as e:
        logger.critical("Chainlit data layer initialization failed", exc_info=True)
        raise RuntimeError(f"Failed to initialize Chainlit data layer: {e}") from e


async def perform_startup_health_checks():
    """Perform strict health checks on critical components."""
    logger.info("[HEALTH] Performing strict startup health checks...")

    # Check MCP if enabled
    mcp_url = os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777")
    mcp_enabled = os.getenv("ZEKALAB_MCP_ENABLED", "false").lower() == "true"

    # Check Auth Secret
    if os.getenv("CHAINLIT_AUTH_SECRET"):
        logger.info("[OK] CHAINLIT_AUTH_SECRET is set")
    else:
        logger.warning(
            "[WARN] CHAINLIT_AUTH_SECRET is MISSING! Sessions may not persist or auth may fail."
        )

    # Check Google OAuth
    google_client_id = os.getenv("OAUTH_GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")

    if google_client_id:
        if not google_client_secret:
            logger.critical(
                "[FAIL] OAUTH_GOOGLE_CLIENT_ID is set but OAUTH_GOOGLE_CLIENT_SECRET is MISSING!"
            )
            raise RuntimeError("Google OAuth configuration incomplete: Missing Client Secret")

        logger.info("[OK] Google OAuth Configured")

        # Calculate and log Redirect URI for easy verification
        # Chainlit constructs it as: {CHAINLIT_URL}/auth/oauth/google/callback
        # If CHAINLIT_URL is not set, it defaults to http://localhost:8000 (usually)
        # but in our case likely http://localhost:8501

        chainlit_url = os.getenv("CHAINLIT_URL", "http://localhost:8501")
        redirect_uri = f"{chainlit_url}/auth/oauth/google/callback"

        logger.info("=" * 60)
        logger.info(f"GOOGLE OAUTH REDIRECT URI: {redirect_uri}")
        logger.info("Ensure this EXACT URI is added to your Google Cloud Console!")
        logger.info("=" * 60)

    else:
        logger.info("[INFO] Google OAuth NOT configured (Anonymous mode)")

    if mcp_enabled:
        logger.info(f"Checking Critical MCP Server: {mcp_url}")
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{mcp_url}/health")
                if resp.status_code != 200:
                    raise RuntimeError(f"MCP Health check returned {resp.status_code}")
                logger.info("[OK] ZekaLab MCP Server is ONLINE")
        except Exception as e:
            logger.critical(f"[FAIL] CRITICAL: ZekaLab MCP Server is DOWN at {mcp_url}")
            logger.critical("Set ZEKALAB_MCP_ENABLED=false if you want to run without it.")
            raise RuntimeError(f"Critical dependency missing: ZekaLab MCP ({e})") from e

    logger.info("[OK] All strict startup checks passed.")
