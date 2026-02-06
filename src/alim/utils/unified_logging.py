# src/alim/utils/unified_logging.py
"""Unified logging utility for all ALİM services.

This module provides a consistent way to log to both console and a unified
log file (logs/alim_unified.log) across all services:
- FastAPI (API)
- Chainlit (UI)
- LangGraph (Agent)
- MCP Server

Usage:
    from alim.utils.unified_logging import setup_unified_logging
    setup_unified_logging(service_name="API")
"""

import logging
import os
import sys
from pathlib import Path

# Determine project root (works from src/alim or any subdirectory)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # src/alim/utils -> project root
_LOGS_DIR = _PROJECT_ROOT / "logs"
_UNIFIED_LOG = _LOGS_DIR / "alim_unified.log"


def setup_unified_logging(
    service_name: str = "ALIM",
    level: str = "INFO",
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """Configure unified logging with console and file output.

    Args:
        service_name: Name prefix for log entries (e.g., "API", "UI", "MCP")
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to log to console (stdout)
        file: Whether to log to unified file (logs/alim_unified.log)

    Returns:
        Configured logger instance
    """
    # Set service name in environment for structlog processors
    os.environ["ALIM_SERVICE_NAME"] = service_name

    # Get or create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    logger.handlers = []

    # Format with service name prefix
    log_format = f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        logger.addHandler(console_handler)

    # File handler (unified log)
    if file:
        try:
            _LOGS_DIR.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(
                _UNIFIED_LOG,
                mode="a",  # Append mode
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup unified file logging: {e}", file=sys.stderr)

    return logger


def get_unified_log_path() -> Path:
    """Get the path to the unified log file."""
    return _UNIFIED_LOG


def clear_unified_log() -> None:
    """Clear the unified log file."""
    try:
        _LOGS_DIR.mkdir(exist_ok=True)
        with open(_UNIFIED_LOG, "w", encoding="utf-8") as f:
            f.write("")
    except Exception as e:
        print(f"Warning: Could not clear unified log: {e}", file=sys.stderr)


def append_to_unified_log(message: str, service_name: str = "SYSTEM") -> None:
    """Directly append a message to the unified log (for non-Python output).

    Args:
        message: The message to log
        service_name: Service prefix for the log entry
    """
    try:
        _LOGS_DIR.mkdir(exist_ok=True)
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_UNIFIED_LOG, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} [{service_name}] {message}\n")
    except Exception:
        pass  # Silent fail for logging
