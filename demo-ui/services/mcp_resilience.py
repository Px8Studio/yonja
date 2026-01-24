"""MCP resilience layer with retry logic and graceful degradation.

This module handles:
- MCP server initialization with exponential backoff retry
- Graceful fallback if MCP is unavailable (continue without tools)
- Health check monitoring
- User notifications about service status

Architectural Role:
    The base `MCPClient` (`src/yonca/mcp/client.py`) lacks retry logic and only
    handles single-request timeouts. `MCPResilienceManager` implements the
    necessary retry-with-backoff loop to prevent the UI from crashing if the
    MCP server is slightly slow to start.
"""

import asyncio
import logging
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class MCPResilienceManager:
    """Manages MCP initialization with retry logic and graceful degradation."""

    def __init__(
        self,
        mcp_url: str = "http://localhost:7777",
        health_endpoint: str = "/health",
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
    ):
        """Initialize resilience manager.

        Args:
            mcp_url: Base URL of MCP server
            health_endpoint: Health check endpoint path
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            backoff_factor: Exponential backoff multiplier
        """
        self.mcp_url = mcp_url
        self.health_endpoint = health_endpoint
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

        # State
        self.is_available = False
        self.last_check_time: datetime | None = None
        self.last_error: str | None = None
        self.retry_count = 0

    async def health_check(self) -> bool:
        """Perform single health check.

        Returns:
            True if server is responding, False otherwise
        """
        url = f"{self.mcp_url}{self.health_endpoint}"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(url)
                is_healthy = response.status_code == 200
                self.last_check_time = datetime.now()

                if is_healthy:
                    self.last_error = None
                    logger.debug(f"MCP health ok: url={url}")
                else:
                    self.last_error = f"HTTP {response.status_code}"
                    logger.warning(f"MCP health degraded: url={url}, status={response.status_code}")

                return is_healthy

        except TimeoutError:
            self.last_error = "Timeout (2s)"
            logger.warning(f"MCP health timeout: url={url}")
            return False
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"MCP health error: url={url}, error={str(e)}")
            return False

    async def initialize_with_retry(self) -> bool:
        """Initialize MCP with exponential backoff retry.

        On first failure, retries with delays:
        - Attempt 1: Immediate
        - Attempt 2: 1 second delay
        - Attempt 3: 2 seconds delay
        - Attempt 4: 4 seconds delay
        - etc...

        Total time for 3 retries: ~1s + 2s + 4s = ~7 seconds max

        Returns:
            True if MCP initialized successfully, False if all retries failed
        """
        self.retry_count = 0

        for attempt in range(self.max_retries):
            self.retry_count = attempt + 1

            if await self.health_check():
                self.is_available = True
                logger.info(
                    f"MCP initialization success: url={self.mcp_url}, attempt={self.retry_count}"
                )
                return True

            # Calculate backoff delay for next retry
            if attempt < self.max_retries - 1:
                delay = min(
                    self.initial_delay * (self.backoff_factor**attempt),
                    self.max_delay,
                )
                logger.warning(
                    f"MCP initialization retry: url={self.mcp_url}, attempt={self.retry_count}, next_retry_in_seconds={delay}, error={self.last_error}"
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        self.is_available = False
        logger.error(
            f"MCP initialization failed: url={self.mcp_url}, attempts={self.retry_count}, last_error={self.last_error}"
        )
        return False

    def get_status(self) -> dict:
        """Get current MCP status.

        Returns:
            Dict with status information for logging/debugging
        """
        return {
            "available": self.is_available,
            "url": self.mcp_url,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_error": self.last_error,
            "retry_attempts": self.retry_count,
        }

    async def ensure_available(self, allow_degraded: bool = True) -> bool:
        """Ensure MCP is available, retry if needed, optionally degrade if unavailable.

        This is the main method to call before accessing MCP tools.

        Args:
            allow_degraded: If True, return True even if MCP unavailable (graceful
                           degradation). If False, only return True if actually available.

        Returns:
            True if available OR degradation allowed, False if must fail
        """
        if not self.is_available:
            # Try to initialize/reconnect
            await self.initialize_with_retry()

        # If still not available but degradation allowed, continue anyway
        if not self.is_available and allow_degraded:
            logger.warning(
                f"MCP degraded mode: url={self.mcp_url}, reason=MCP unavailable but degradation allowed"
            )
            return True  # Signal: continue without tools

        return self.is_available


# ============================================
# SINGLETON INSTANCE
# ============================================
# Create single instance that persists across requests
_mcp_manager: MCPResilienceManager | None = None


def get_mcp_manager(
    mcp_url: str = "http://localhost:7777",
) -> MCPResilienceManager:
    """Get or create singleton MCP resilience manager.

    Args:
        mcp_url: Base URL of MCP server

    Returns:
        MCPResilienceManager instance
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPResilienceManager(mcp_url=mcp_url)
    return _mcp_manager


# ============================================
# USAGE HELPERS
# ============================================


async def initialize_mcp(mcp_url: str = "http://localhost:7777") -> bool:
    """Initialize MCP on startup.

    Call this in @cl.on_chat_start to ensure MCP is available.

    Args:
        mcp_url: Base URL of MCP server

    Returns:
        True if initialization successful or degradation allowed
    """
    manager = get_mcp_manager(mcp_url=mcp_url)
    return await manager.initialize_with_retry()


async def ensure_mcp_available(mcp_url: str = "http://localhost:7777") -> bool:
    """Check if MCP is available, with graceful degradation.

    Use this before calling MCP tools. If MCP is unavailable, returns True anyway
    so the chat can continue without tools.

    Args:
        mcp_url: Base URL of MCP server

    Returns:
        True (always, for graceful degradation)
    """
    manager = get_mcp_manager(mcp_url=mcp_url)
    return await manager.ensure_available(allow_degraded=True)


def get_mcp_status(mcp_url: str = "http://localhost:7777") -> dict:
    """Get current MCP status for debugging/logging.

    Args:
        mcp_url: Base URL of MCP server

    Returns:
        Dict with status information
    """
    manager = get_mcp_manager(mcp_url=mcp_url)
    return manager.get_status()


# ============================================
# ERROR HANDLING HELPERS
# ============================================


async def call_mcp_tool_safe(
    tool_name: str,
    tool_func,
    *args,
    fallback_result=None,
    mcp_url: str = "http://localhost:7777",
    **kwargs,
):
    """Call an MCP tool with error handling and fallback.

    If MCP is unavailable or the call fails, returns fallback_result
    instead of raising an exception.

    Args:
        tool_name: Name of tool for logging
        tool_func: Async function to call
        *args: Positional arguments for tool_func
        fallback_result: Value to return if tool fails
        mcp_url: Base URL of MCP server
        **kwargs: Keyword arguments for tool_func

    Returns:
        Result from tool_func or fallback_result if failed
    """
    try:
        # Ensure MCP is available (with degradation)
        await ensure_mcp_available(mcp_url=mcp_url)

        # Call the tool
        result = await tool_func(*args, **kwargs)
        logger.debug(f"MCP tool success: tool={tool_name}")
        return result

    except Exception as e:
        logger.warning(
            f"MCP tool error: tool={tool_name}, error={str(e)}, using_fallback={fallback_result is not None}"
        )
        return fallback_result


# ============================================
# STATUS REPORTING
# ============================================


def format_mcp_status_for_ui(mcp_url: str = "http://localhost:7777") -> str:
    """Format MCP status as user-friendly message for UI.

    Args:
        mcp_url: Base URL of MCP server

    Returns:
        Markdown-formatted status string
    """
    status = get_mcp_status(mcp_url=mcp_url)

    if status["available"]:
        return "✅ MCP tools available"
    else:
        error_info = f" ({status['last_error']})" if status["last_error"] else ""
        return f"⚠️ MCP tools unavailable{error_info} - chat continues without tools"
