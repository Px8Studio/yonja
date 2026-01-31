import logging
import sys
from typing import Any

import structlog


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, output logs as JSON. If False, use console-friendly text.
    """

    # 1. Configure Standard Library Logging
    # Force reconfiguration to override Uvicorn/Chainlit defaults

    root_logger = logging.getLogger()
    root_logger.handlers = []  # Clear existing handlers

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,  # Python 3.8+ force
    )

    # 2. Configure Structlog Processors
    # These processors transform the log event before rendering.

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,  # Support async context
        structlog.stdlib.filter_by_level,  # Filter by log level
        structlog.stdlib.add_logger_name,  # Add logger name
        structlog.stdlib.add_log_level,  # Add log level
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 timestamps
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,  # Format exceptions
        structlog.processors.UnicodeDecoder(),
    ]

    # 3. Choose Renderer
    # JSON for production/files, Console for local dev (if requested, but user wanted native/future proof)
    # We will stick to the user's request for "future proof" (likely JSON) but
    # allow a flag if they ever want pretty text back.

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # 4. Apply Configuration
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),  # Use standard library logger factory
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Silence overly verbose loggers if needed (optional)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> Any:
    """
    Get a structured logger instance.
    Usage:
        from services.logger import get_logger
        logger = get_logger(__name__)
        logger.info("event", key="value")
    """
    return structlog.get_logger(name)
