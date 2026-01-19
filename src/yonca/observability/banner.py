# src/yonca/observability/banner.py
"""Rich terminal banners and startup displays for demo impressions.

Uses ANSI escape codes for colors and formatting that work in:
- VS Code terminal
- Windows Terminal
- PowerShell
- Most modern terminals

Example usage:
    from yonca.observability.banner import print_startup_banner, print_status_line
    
    print_startup_banner("api")
    print_status_line("PostgreSQL", "Connected", "success", "localhost:5433")
"""

import sys
from dataclasses import dataclass
from typing import Optional


# ══════════════════════════════════════════════════════════════
# ANSI Color Codes (Windows Terminal / VS Code compatible)
# ══════════════════════════════════════════════════════════════

class Colors:
    """ANSI escape codes for terminal colors."""
    # Reset
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background colors
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


# ══════════════════════════════════════════════════════════════
# Status Symbols
# ══════════════════════════════════════════════════════════════

@dataclass
class StatusStyle:
    """Style configuration for status display."""
    symbol: str
    color: str
    label: str


STATUS_STYLES = {
    "success": StatusStyle("✓", Colors.BRIGHT_GREEN, "OK"),
    "warning": StatusStyle("⚠", Colors.BRIGHT_YELLOW, "WARN"),
    "error": StatusStyle("✗", Colors.BRIGHT_RED, "FAIL"),
    "info": StatusStyle("ℹ", Colors.BRIGHT_CYAN, "INFO"),
    "pending": StatusStyle("◌", Colors.BRIGHT_YELLOW, "..."),
    "running": StatusStyle("●", Colors.BRIGHT_GREEN, "LIVE"),
}


# ══════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════

def _c(text: str, color: str) -> str:
    """Colorize text with ANSI codes."""
    return f"{color}{text}{Colors.RESET}"


def _bold(text: str) -> str:
    """Make text bold."""
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def _dim(text: str) -> str:
    """Make text dim/gray."""
    return f"{Colors.DIM}{text}{Colors.RESET}"


def _link(url: str, display_text: Optional[str] = None) -> str:
    """Create clickable terminal link (OSC 8 hyperlinks).
    
    Works in:
    - VS Code terminal ✓
    - Windows Terminal ✓
    - iTerm2 ✓
    - Many modern terminals
    
    Falls back to plain URL in unsupported terminals.
    """
    display = display_text or url
    # OSC 8 hyperlink format: \033]8;;URL\033\\TEXT\033]8;;\033\\
    return f"\033]8;;{url}\033\\{Colors.UNDERLINE}{Colors.BRIGHT_CYAN}{display}{Colors.RESET}\033]8;;\033\\"


# ══════════════════════════════════════════════════════════════
# Startup Banners
# ══════════════════════════════════════════════════════════════

YONCA_ASCII = r"""
  ╭─────────────────────────────────────────────────╮
  │  🌿 YONCA AI — Kənd Təsərrüfatı Köməkçisi 🌾    │
  ╰─────────────────────────────────────────────────╯
"""

YONCA_ASCII_COMPACT = "🌿 YONCA AI — Kənd Təsərrüfatı Köməkçisi"


def print_startup_banner(
    component: str = "api",
    version: str = "1.0.0",
    mode: str = "development",
) -> None:
    """Print a beautiful startup banner.
    
    Args:
        component: "api", "demo-ui", or "agent"
        version: Application version
        mode: "development", "production", or "demo"
    """
    component_info = {
        "api": ("FastAPI Server", "🚀", Colors.BRIGHT_GREEN),
        "demo-ui": ("Chainlit Demo", "🖥️", Colors.BRIGHT_CYAN),
        "agent": ("LangGraph Agent", "🤖", Colors.BRIGHT_MAGENTA),
    }
    
    name, emoji, color = component_info.get(component, ("Service", "⚡", Colors.WHITE))
    
    print()
    print(_c("  ╭─────────────────────────────────────────────────────────╮", Colors.BRIGHT_GREEN))
    print(_c("  │", Colors.BRIGHT_GREEN) + _c(f"  🌿 YONCA AI — Kənd Təsərrüfatı Köməkçisi              ", Colors.BRIGHT_WHITE) + _c("│", Colors.BRIGHT_GREEN))
    print(_c("  │", Colors.BRIGHT_GREEN) + _c(f"     {emoji} {name} v{version}", color) + " " * (44 - len(name) - len(version)) + _c("│", Colors.BRIGHT_GREEN))
    print(_c("  ╰─────────────────────────────────────────────────────────╯", Colors.BRIGHT_GREEN))
    print()


def print_section_header(title: str) -> None:
    """Print a section header with visual separation."""
    print()
    print(_c("  ─────────────────────────────────────────────────────────", Colors.DIM))
    print(_c(f"  {title}", Colors.BRIGHT_WHITE + Colors.BOLD))
    print(_c("  ─────────────────────────────────────────────────────────", Colors.DIM))


def print_status_line(
    component: str,
    status: str,
    style: str = "info",
    detail: Optional[str] = None,
    url: Optional[str] = None,
) -> None:
    """Print a formatted status line.
    
    Args:
        component: Component name (e.g., "PostgreSQL", "Redis")
        status: Status text (e.g., "Connected", "Ready")
        style: One of: success, warning, error, info, pending, running
        detail: Optional detail text (e.g., "localhost:5433")
        url: Optional clickable URL
        
    Example outputs:
        ✓ PostgreSQL    Connected           localhost:5433
        ⚠ Redis         Not Available       sessions will be stateless
        ● API           Running             http://localhost:8000
    """
    st = STATUS_STYLES.get(style, STATUS_STYLES["info"])
    
    symbol = _c(st.symbol, st.color)
    comp_text = f"{component:<14}"
    status_text = _c(f"{status:<20}", st.color)
    
    line = f"  {symbol} {comp_text} {status_text}"
    
    if url:
        line += f" {_link(url)}"
    elif detail:
        line += f" {_dim(detail)}"
    
    print(line)


def print_status_table(items: list[dict]) -> None:
    """Print a formatted status table.
    
    Args:
        items: List of dicts with keys: component, status, style, detail, url
        
    Example:
        items = [
            {"component": "PostgreSQL", "status": "Connected", "style": "success", "detail": "localhost:5433"},
            {"component": "Redis", "status": "Connected", "style": "success"},
        ]
    """
    for item in items:
        print_status_line(**item)


def print_endpoints(endpoints: list[tuple[str, str, str]]) -> None:
    """Print endpoint information with clickable links.
    
    Args:
        endpoints: List of (name, url, description) tuples
        
    Example:
        endpoints = [
            ("API", "http://localhost:8000", "REST endpoints"),
            ("Docs", "http://localhost:8000/docs", "Swagger UI"),
        ]
    """
    print()
    print(_c("  📡 Endpoints:", Colors.BRIGHT_WHITE))
    print()
    for name, url, description in endpoints:
        print(f"     {_c(f'{name}:', Colors.BRIGHT_CYAN)} {_link(url)}")
        if description:
            print(f"          {_dim(description)}")


def print_quick_links(links: list[tuple[str, str]]) -> None:
    """Print quick access links in a compact format.
    
    Args:
        links: List of (name, url) tuples
    """
    print()
    print(_c("  🔗 Quick Links:", Colors.BRIGHT_WHITE))
    link_parts = [f"{_link(url, name)}" for name, url in links]
    print(f"     {' │ '.join(link_parts)}")


def print_shutdown_message() -> None:
    """Print a clean shutdown message."""
    print()
    print(_c("  ╭─────────────────────────────────────────╮", Colors.BRIGHT_YELLOW))
    print(_c("  │  🌿 Yonca AI shutting down gracefully   │", Colors.BRIGHT_YELLOW))
    print(_c("  ╰─────────────────────────────────────────╯", Colors.BRIGHT_YELLOW))


def print_startup_complete(service_name: str = "Yonca AI") -> None:
    """Print startup complete message."""
    print()
    print(_c("  ═══════════════════════════════════════════════════════", Colors.BRIGHT_GREEN))
    print(_c(f"  ✅ {service_name} ready and accepting connections!", Colors.BRIGHT_GREEN))
    print(_c("  ═══════════════════════════════════════════════════════", Colors.BRIGHT_GREEN))
    print()


# ══════════════════════════════════════════════════════════════
# Specialized Banners
# ══════════════════════════════════════════════════════════════

def print_llm_info(
    provider: str,
    model: str,
    mode: str = "cloud",
    base_url: Optional[str] = None,
) -> None:
    """Print LLM configuration information.
    
    Args:
        provider: LLM provider name (e.g., "Groq", "Ollama", "Gemini")
        model: Model identifier
        mode: "cloud", "local", or "hybrid"
        base_url: Optional API base URL
    """
    print_section_header("🤖 LLM Configuration")
    
    mode_colors = {
        "cloud": Colors.BRIGHT_CYAN,
        "local": Colors.BRIGHT_GREEN,
        "hybrid": Colors.BRIGHT_MAGENTA,
    }
    mode_labels = {
        "cloud": "☁️  Cloud API",
        "local": "🏠 Local (Self-hosted)",
        "hybrid": "🔄 Hybrid",
    }
    
    print_status_line("Provider", provider, "info")
    print_status_line("Model", model, "success")
    print_status_line("Mode", mode_labels.get(mode, mode), "info")
    
    if base_url:
        print_status_line("Endpoint", base_url, "info", url=base_url)


def print_database_info(
    postgres_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    postgres_ok: bool = True,
    redis_ok: bool = True,
) -> None:
    """Print database connection status.
    
    Args:
        postgres_url: PostgreSQL connection info (masked)
        redis_url: Redis connection URL
        postgres_ok: Whether PostgreSQL is connected
        redis_ok: Whether Redis is connected
    """
    print_section_header("🗄️  Data Layer")
    
    if postgres_url:
        # Extract host:port from URL, mask password
        try:
            host_part = postgres_url.split("@")[-1].split("/")[0]
        except Exception:
            host_part = "configured"
        
        print_status_line(
            "PostgreSQL",
            "Connected" if postgres_ok else "Failed",
            "success" if postgres_ok else "error",
            host_part,
        )
    
    if redis_url:
        try:
            host_part = redis_url.replace("redis://", "").split("/")[0]
        except Exception:
            host_part = "configured"
        
        print_status_line(
            "Redis",
            "Connected" if redis_ok else "Not Available",
            "success" if redis_ok else "warning",
            host_part + " (checkpointing)" if redis_ok else "sessions stateless",
        )


# ══════════════════════════════════════════════════════════════
# Entry point for testing
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Demo all banner styles
    print_startup_banner("api", "1.0.0", "development")
    
    print_section_header("🔌 Infrastructure")
    print_status_line("Docker", "Running", "running", "5 containers")
    print_status_line("PostgreSQL", "Connected", "success", "localhost:5433")
    print_status_line("Redis", "Connected", "success", "localhost:6379")
    print_status_line("Ollama", "Ready", "success", "qwen3:4b loaded")
    print_status_line("Langfuse", "Connected", "success", "localhost:3001")
    
    print_llm_info("Groq", "llama-4-maverick-17b-128e-instruct", "cloud")
    
    print_endpoints([
        ("API", "http://localhost:8000", "REST endpoints"),
        ("Swagger", "http://localhost:8000/docs", "Interactive API docs"),
        ("Chat UI", "http://localhost:8501", "Demo interface"),
        ("Langfuse", "http://localhost:3001", "LLM observability"),
    ])
    
    print_quick_links([
        ("Swagger", "http://localhost:8000/docs"),
        ("Chat", "http://localhost:8501"),
        ("Traces", "http://localhost:3001"),
    ])
    
    print_startup_complete("Yonca AI API")
