# src/yonca/observability/langfuse.py
"""Langfuse integration for self-hosted LLM observability.

Langfuse is an open-source alternative to LangSmith that provides:
- Full LangGraph/LangChain tracing with zero code changes
- Prompt versioning and management
- Cost tracking per model/user
- Evaluation datasets for regression testing
- 100% data residency (self-hosted)

Setup:
1. Start Langfuse: docker-compose -f docker-compose.local.yml up langfuse-server langfuse-db
2. Open http://localhost:3001 and create an account
3. Go to Settings → API Keys → Create new keys
4. Set YONCA_LANGFUSE_SECRET_KEY and YONCA_LANGFUSE_PUBLIC_KEY in .env

Dashboard Features:
- Traces: See every LangGraph node execution with timing
- Sessions: Group conversations by thread_id
- Users: Track per-farmer usage patterns
- Scores: Add quality ratings for evaluation
- Prompts: Version control your system prompts
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from langfuse import Langfuse
    from langfuse.callback import CallbackHandler

logger = logging.getLogger(__name__)


# ============================================================
# Langfuse Client Management
# ============================================================

_langfuse_client: "Langfuse | None" = None


def get_langfuse_client() -> "Langfuse | None":
    """Get or create the Langfuse client singleton.
    
    Returns:
        Langfuse client if configured and enabled, None otherwise.
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        return _langfuse_client
    
    from yonca.config import settings
    
    if not settings.langfuse_enabled:
        logger.debug("Langfuse disabled via settings")
        return None
    
    if not settings.langfuse_secret_key or not settings.langfuse_public_key:
        logger.warning(
            "Langfuse enabled but API keys not configured. "
            "Set YONCA_LANGFUSE_SECRET_KEY and YONCA_LANGFUSE_PUBLIC_KEY. "
            "Get keys from Langfuse UI → Settings → API Keys"
        )
        return None
    
    try:
        from langfuse import Langfuse
        
        _langfuse_client = Langfuse(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host,
            debug=settings.langfuse_debug,
            sample_rate=settings.langfuse_sample_rate,
        )
        
        logger.info(
            f"Langfuse initialized: {settings.langfuse_host} "
            f"(sample_rate={settings.langfuse_sample_rate})"
        )
        return _langfuse_client
        
    except ImportError:
        logger.error("langfuse package not installed. Run: poetry add langfuse")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return None


def shutdown_langfuse() -> None:
    """Flush and shutdown Langfuse client.
    
    Call this on application shutdown to ensure all traces are sent.
    """
    global _langfuse_client
    
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
            _langfuse_client.shutdown()
            logger.info("Langfuse shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Langfuse: {e}")
        finally:
            _langfuse_client = None


# ============================================================
# LangChain/LangGraph Callback Handler
# ============================================================

def create_langfuse_handler(
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    trace_name: str | None = None,
) -> "CallbackHandler | None":
    """Create a Langfuse callback handler for LangGraph tracing.
    
    This handler automatically captures:
    - Every LangGraph node execution with timing
    - LLM calls (prompts, completions, tokens, costs)
    - Tool/function calls
    - Errors and exceptions
    
    Args:
        session_id: Conversation thread ID (groups turns together)
        user_id: User identifier (for per-user analytics)
        tags: List of tags for filtering traces
        metadata: Additional metadata (farm_id, region, etc.)
        trace_name: Custom name for the trace
        
    Returns:
        CallbackHandler if Langfuse is configured, None otherwise.
        
    Example:
        ```python
        handler = create_langfuse_handler(
            session_id=thread_id,
            user_id=user_id,
            tags=["production", "agronomist"],
            metadata={"farm_id": "farm_123", "region": "Baku"}
        )
        
        config = {"callbacks": [handler]} if handler else {}
        result = await graph.ainvoke(state, config=config)
        ```
    """
    from yonca.config import settings
    
    if not settings.langfuse_enabled:
        return None
    
    if not settings.langfuse_secret_key or not settings.langfuse_public_key:
        return None
    
    try:
        from langfuse.callback import CallbackHandler
        
        handler = CallbackHandler(
            secret_key=settings.langfuse_secret_key,
            public_key=settings.langfuse_public_key,
            host=settings.langfuse_host,
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
            trace_name=trace_name,
            debug=settings.langfuse_debug,
            sample_rate=settings.langfuse_sample_rate,
        )
        
        return handler
        
    except ImportError:
        logger.warning("langfuse package not installed")
        return None
    except Exception as e:
        logger.error(f"Failed to create Langfuse handler: {e}")
        return None


# ============================================================
# Trace Context Manager
# ============================================================

@contextmanager
def langfuse_trace(
    name: str,
    session_id: str | None = None,
    user_id: str | None = None,
    input_data: Any = None,
    metadata: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    """Context manager for creating Langfuse traces.
    
    Use this for tracing non-LangChain code (custom functions, API calls, etc.)
    
    Args:
        name: Name of the trace/span
        session_id: Conversation thread ID
        user_id: User identifier
        input_data: Input to log
        metadata: Additional metadata
        
    Yields:
        Langfuse trace object (or None if disabled)
        
    Example:
        ```python
        with langfuse_trace("weather_api_call", session_id=thread_id) as trace:
            result = await fetch_weather(location)
            if trace:
                trace.update(output=result)
        ```
    """
    client = get_langfuse_client()
    
    if client is None:
        yield None
        return
    
    try:
        trace = client.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            input=input_data,
            metadata=metadata or {},
        )
        yield trace
        
    except Exception as e:
        logger.error(f"Langfuse trace error: {e}")
        yield None


# ============================================================
# Scoring / Evaluation Helpers
# ============================================================

def score_trace(
    trace_id: str,
    name: str,
    value: float,
    comment: str | None = None,
) -> bool:
    """Add a score to a trace for evaluation.
    
    Scores are used to build evaluation datasets and track quality over time.
    
    Args:
        trace_id: The Langfuse trace ID
        name: Score name (e.g., "accuracy", "relevance", "language_quality")
        value: Score value (typically 0-1 or 1-5)
        comment: Optional explanation
        
    Returns:
        True if score was recorded successfully
        
    Example:
        ```python
        # After getting user feedback
        score_trace(
            trace_id=response.trace_id,
            name="user_rating",
            value=4.0,
            comment="Helpful advice on irrigation"
        )
        ```
    """
    client = get_langfuse_client()
    
    if client is None:
        return False
    
    try:
        client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to record score: {e}")
        return False


# ============================================================
# Utility Functions
# ============================================================

def is_langfuse_healthy() -> bool:
    """Check if Langfuse connection is healthy.
    
    Returns:
        True if Langfuse is reachable and authenticated
    """
    client = get_langfuse_client()
    
    if client is None:
        return False
    
    try:
        # Simple health check - auth will fail if keys are wrong
        client.auth_check()
        return True
    except Exception:
        return False


def get_langfuse_trace_url(trace_id: str) -> str | None:
    """Get the direct URL to a trace in the Langfuse UI.
    
    Args:
        trace_id: The trace ID
        
    Returns:
        URL to the trace in Langfuse dashboard
    """
    from yonca.config import settings
    
    if not settings.langfuse_enabled:
        return None
    
    return f"{settings.langfuse_host}/trace/{trace_id}"
