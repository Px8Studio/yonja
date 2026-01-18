# src/yonca/observability/__init__.py
"""Observability module for Yonca AI.

Provides self-hosted LLM tracing, metrics, and monitoring
with 100% data residency control via Langfuse.

Quick Start:
1. Start Langfuse: docker-compose -f docker-compose.local.yml up langfuse-server langfuse-db -d
2. Open http://localhost:3001 and create an account
3. Get API keys from Settings → API Keys
4. Add to .env:
   YONCA_LANGFUSE_SECRET_KEY=sk-lf-...
   YONCA_LANGFUSE_PUBLIC_KEY=pk-lf-...

Usage:
    from yonca.observability import create_langfuse_handler
    
    handler = create_langfuse_handler(
        session_id=thread_id,
        user_id=user_id,
        tags=["production"],
    )
    
    config = {"callbacks": [handler]} if handler else {}
    result = await graph.ainvoke(state, config=config)
"""

from yonca.observability.langfuse import (
    create_langfuse_handler,
    get_langfuse_client,
    get_langfuse_trace_url,
    is_langfuse_healthy,
    langfuse_trace,
    score_trace,
    shutdown_langfuse,
)

__all__ = [
    "create_langfuse_handler",
    "get_langfuse_client",
    "get_langfuse_trace_url",
    "is_langfuse_healthy",
    "langfuse_trace",
    "score_trace",
    "shutdown_langfuse",
]