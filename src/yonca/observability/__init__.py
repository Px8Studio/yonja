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

from yonca.observability.banner import (
    Colors,
    format_trace_link,
    print_database_info,
    print_endpoints,
    print_infrastructure_summary,
    print_infrastructure_tier,
    print_llm_info,
    print_model_capabilities,
    print_observability_info,
    print_quick_links,
    print_section_header,
    print_security_info,
    print_shutdown_message,
    print_startup_banner,
    print_startup_complete,
    print_status_line,
    print_status_table,
    print_tier_comparison,
    print_trace_info,
)
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
    # Langfuse
    "create_langfuse_handler",
    "get_langfuse_client",
    "get_langfuse_trace_url",
    "is_langfuse_healthy",
    "langfuse_trace",
    "score_trace",
    "shutdown_langfuse",
    # Banners
    "print_startup_banner",
    "print_section_header",
    "print_status_line",
    "print_status_table",
    "print_endpoints",
    "print_quick_links",
    "print_shutdown_message",
    "print_startup_complete",
    "print_llm_info",
    "print_database_info",
    "print_infrastructure_summary",
    "print_model_capabilities",
    "print_security_info",
    "print_observability_info",
    "print_infrastructure_tier",
    "print_tier_comparison",
    "format_trace_link",
    "print_trace_info",
    "Colors",
]
