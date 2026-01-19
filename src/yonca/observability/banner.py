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
  │  🌿 YONCA AI — Kənd Təsərrüfatı Köməkçisi       │
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
    api_key_set: bool = False,
    features: Optional[list[str]] = None,
) -> None:
    """Print LLM configuration information.
    
    Args:
        provider: LLM provider name (e.g., "Groq", "Ollama", "Gemini")
        model: Model identifier
        mode: "cloud", "local", or "hybrid"
        base_url: Optional API base URL
        api_key_set: Whether API key is configured
        features: Optional list of model features/capabilities
    """
    print_section_header("🤖 LLM Configuration")
    
    mode_labels = {
        "cloud": "☁️  Cloud API",
        "local": "🏠 Self-Hosted",
        "hybrid": "🔄 Hybrid",
        "open_source": "🌐 Open-Source (via Cloud)",
    }
    
    print_status_line("Provider", provider, "success")
    print_status_line("Model", model, "info")
    print_status_line("Mode", mode_labels.get(mode, mode), "info")
    
    if api_key_set:
        print_status_line("API Key", "Configured ✓", "success")
    elif mode == "local":
        print_status_line("API Key", "Not required (local)", "info")
    else:
        print_status_line("API Key", "Missing!", "warning")
    
    if base_url:
        print_status_line("Endpoint", base_url, "info")
    
    if features:
        print()
        print(_c("  📋 Model Capabilities:", Colors.BRIGHT_WHITE))
        for feature in features:
            print(f"     {_c('•', Colors.BRIGHT_GREEN)} {feature}")


def print_database_info(
    postgres_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    postgres_ok: bool = True,
    redis_ok: bool = True,
    langfuse_url: Optional[str] = None,
    langfuse_ok: bool = False,
) -> None:
    """Print database connection status.
    
    Args:
        postgres_url: PostgreSQL connection info (masked)
        redis_url: Redis connection URL
        postgres_ok: Whether PostgreSQL is connected
        redis_ok: Whether Redis is connected
        langfuse_url: Langfuse observability URL
        langfuse_ok: Whether Langfuse is configured
    """
    print_section_header("🗄️  Data Layer")
    
    if postgres_url:
        # Extract host:port from URL, mask password
        try:
            host_part = postgres_url.split("@")[-1].split("/")[0]
            db_name = postgres_url.split("/")[-1].split("?")[0]
        except Exception:
            host_part = "configured"
            db_name = "yonca"
        
        print_status_line(
            "PostgreSQL",
            "Connected" if postgres_ok else "Failed",
            "success" if postgres_ok else "error",
            f"{host_part}/{db_name}",
        )
    
    if redis_url:
        try:
            host_part = redis_url.replace("redis://", "").split("/")[0]
            db_num = redis_url.split("/")[-1] if "/" in redis_url else "0"
        except Exception:
            host_part = "configured"
            db_num = "0"
        
        print_status_line(
            "Redis",
            "Connected" if redis_ok else "Not Available",
            "success" if redis_ok else "warning",
            f"{host_part}/db{db_num} (checkpointing)" if redis_ok else "sessions stateless",
        )
    
    if langfuse_url:
        print_status_line(
            "Langfuse",
            "Enabled" if langfuse_ok else "Not Configured",
            "success" if langfuse_ok else "warning",
            langfuse_url if langfuse_ok else "set LANGFUSE_SECRET_KEY",
        )


def print_infrastructure_summary(
    services: list[dict],
) -> None:
    """Print infrastructure services summary.
    
    Args:
        services: List of service dicts with: name, status, style, port, detail
    """
    print_section_header("🐳 Infrastructure Services")
    
    for svc in services:
        port_info = f":{svc.get('port')}" if svc.get('port') else ""
        detail = svc.get('detail', '')
        if port_info and detail:
            full_detail = f"localhost{port_info} — {detail}"
        elif port_info:
            full_detail = f"localhost{port_info}"
        else:
            full_detail = detail
            
        print_status_line(
            svc['name'],
            svc['status'],
            svc.get('style', 'info'),
            full_detail,
        )


def print_model_capabilities(model_name: str) -> None:
    """Print model-specific capabilities based on known models."""
    capabilities = {
        "meta-llama/llama-4-maverick-17b-128e-instruct": [
            "🎯 2026 Gold Standard — Single model for ALL tasks",
            "🌍 Native Azerbaijani language support",
            "🧮 Advanced reasoning & calculations",
            "📝 128K context window",
            "⚡ Enterprise-grade latency via Groq LPU",
            "🏠 Self-hostable with appropriate hardware",
        ],
        "llama-3.3-70b-versatile": [
            "🌍 Excellent multilingual support",
            "📝 32K context window",
            "🎯 Best for Azerbaijani quality",
        ],
        "qwen3:4b": [
            "🏠 Local-first, runs on CPU",
            "⚡ Fast inference, low latency",
            "🧮 Good for reasoning tasks",
            "⚠️  Turkish leakage risk",
        ],
        "gemini-2.0-flash-exp": [
            "☁️  Google Cloud API",
            "⚡ Very fast inference",
            "🌍 Good multilingual support",
            "🔒 Proprietary (data leaves region)",
        ],
    }
    
    caps = capabilities.get(model_name)
    if caps:
        print()
        print(_c("  📋 Model Capabilities:", Colors.BRIGHT_WHITE))
        for cap in caps:
            print(f"     {cap}")


def print_security_info(
    rate_limit: int = 30,
    burst_limit: int = 50,
    jwt_configured: bool = False,
    cors_origins: Optional[list[str]] = None,
) -> None:
    """Print security configuration summary."""
    print_section_header("🔒 Security")
    
    print_status_line("Rate Limit", f"{rate_limit} req/min", "info", f"burst: {burst_limit}")
    print_status_line("JWT Auth", "Configured" if jwt_configured else "Dev Mode", "success" if jwt_configured else "warning")
    
    if cors_origins:
        origins_display = ", ".join(cors_origins[:2])
        if len(cors_origins) > 2:
            origins_display += f" +{len(cors_origins) - 2} more"
        print_status_line("CORS", f"{len(cors_origins)} origins", "info", origins_display)


def print_observability_info(
    langfuse_enabled: bool = False,
    langfuse_url: str = "http://localhost:3001",
    prometheus_enabled: bool = False,
    log_level: str = "INFO",
) -> None:
    """Print observability configuration."""
    print_section_header("📊 Observability")
    
    print_status_line(
        "Langfuse",
        "Enabled" if langfuse_enabled else "Disabled",
        "success" if langfuse_enabled else "warning",
        langfuse_url if langfuse_enabled else "LLM tracing disabled",
    )
    
    if prometheus_enabled:
        print_status_line("Prometheus", "Enabled", "success", "/metrics endpoint")
    
    print_status_line("Log Level", log_level, "info")


def print_infrastructure_tier(
    tier_spec: dict,
    show_all_tiers: bool = False,
) -> None:
    """Print ALEM Infrastructure tier information.
    
    Args:
        tier_spec: Tier specification dict from INFERENCE_TIER_SPECS
        show_all_tiers: If True, shows comparison of all tiers
    """
    print_section_header("🏗️  ALEM Infrastructure Tier")
    
    if not tier_spec:
        print_status_line("Tier", "Unknown", "warning", "Configure LLM provider")
        return
    
    icon = tier_spec.get("icon", "⚡")
    name = tier_spec.get("name", "Unknown")
    tagline = tier_spec.get("tagline", "")
    
    # Header line with icon and name
    print()
    print(f"  {_c(f'{icon}  {name}', Colors.BRIGHT_CYAN + Colors.BOLD)}")
    print(f"     {_dim(tagline)}")
    print()
    
    # Specs table
    specs = [
        ("Provider", tier_spec.get("provider", "—")),
        ("Latency", tier_spec.get("latency", "—")),
        ("Throughput", tier_spec.get("throughput", "—")),
        ("Data Residency", tier_spec.get("data_residency", "—")),
        ("Cost Range", tier_spec.get("cost_range", "—")),
    ]
    
    for label, value in specs:
        # Highlight data residency with Azerbaijan flag
        if "Azerbaijan" in value or "🇦🇿" in value:
            print(f"     {_c(f'{label}:', Colors.BRIGHT_WHITE)} {_c(value, Colors.BRIGHT_GREEN)}")
        elif "US" in value or "EU" in value:
            print(f"     {_c(f'{label}:', Colors.BRIGHT_WHITE)} {_c(value, Colors.BRIGHT_YELLOW)}")
        else:
            print(f"     {_c(f'{label}:', Colors.BRIGHT_WHITE)} {value}")
    
    # Models available
    models = tier_spec.get("models", [])
    if models:
        print()
        print(f"     {_c('Models:', Colors.BRIGHT_WHITE)} {', '.join(models)}")
    
    # Use case
    use_case = tier_spec.get("use_case", "")
    if use_case:
        print(f"     {_c('Best for:', Colors.BRIGHT_WHITE)} {_dim(use_case)}")


def print_tier_comparison() -> None:
    """Print a comparison table of all ALEM infrastructure tiers."""
    # Import here to avoid circular import
    from yonca.config import INFERENCE_TIER_SPECS, InferenceTier
    
    print_section_header("🏗️  ALEM Infrastructure Matrix — All Tiers")
    print()
    
    tier_order = [
        InferenceTier.TIER_I_GROQ,
        InferenceTier.TIER_II_GEMINI,
        InferenceTier.TIER_III_SOVEREIGN,
        InferenceTier.TIER_IV_ONPREM,
    ]
    
    for tier in tier_order:
        spec = INFERENCE_TIER_SPECS.get(tier, {})
        icon = spec.get("icon", "•")
        name = spec.get("name", str(tier))
        tagline = spec.get("tagline", "")
        cost = spec.get("cost_range", "")
        residency = spec.get("data_residency", "")
        
        # Color based on data residency
        if "Azerbaijan" in residency:
            color = Colors.BRIGHT_GREEN
            flag = "🇦🇿"
        elif "Customer" in residency:
            color = Colors.BRIGHT_MAGENTA
            flag = "🏠"
        else:
            color = Colors.BRIGHT_YELLOW
            flag = "☁️"
        
        print(f"  {icon} {_c(name, color)}")
        print(f"     {flag} {residency} | {_dim(cost)}")
        print()


# ══════════════════════════════════════════════════════════════
# Langfuse Trace Links (for Chainlit integration)
# ══════════════════════════════════════════════════════════════

def format_trace_link(
    trace_id: str,
    langfuse_host: str = "http://localhost:3001",
    project_name: str = "default",
) -> str:
    """Format a clickable Langfuse trace link.
    
    Args:
        trace_id: The Langfuse trace ID
        langfuse_host: Langfuse server URL
        project_name: Langfuse project name
        
    Returns:
        Formatted clickable link string
    """
    url = f"{langfuse_host}/project/{project_name}/traces/{trace_id}"
    return _link(url, f"🔍 View Trace")


def print_trace_info(
    trace_id: str,
    langfuse_host: str = "http://localhost:3001",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Print trace information with clickable link.
    
    Useful for displaying after LangGraph execution.
    """
    print()
    print(_c("  📊 Trace Recorded:", Colors.BRIGHT_WHITE))
    print(f"     ID: {_dim(trace_id[:16] + '...')}")
    
    if session_id:
        print(f"     Session: {_dim(session_id)}")
    if user_id:
        print(f"     User: {_dim(user_id)}")
    
    url = f"{langfuse_host}/traces/{trace_id}"
    print(f"     {_link(url, '🔗 Open in Langfuse')}")


# ══════════════════════════════════════════════════════════════
# Entry point for testing
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Import config for tier info
    from yonca.config import settings, INFERENCE_TIER_SPECS
    
    # Demo all banner styles
    print_startup_banner("api", "1.0.0", "development")
    
    # LLM Configuration with full details
    print_llm_info(
        provider="Groq (LPU Cloud)",
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        mode="open_source",
        base_url="https://api.groq.com/openai/v1",
        api_key_set=True,
    )
    print_model_capabilities("meta-llama/llama-4-maverick-17b-128e-instruct")
    
    # ALEM Infrastructure Tier
    print_infrastructure_tier(settings.inference_tier_spec)
    
    # Infrastructure
    print_section_header("🔌 Infrastructure")
    print_status_line("PostgreSQL", "Connected", "success", "localhost:5433/yonca — user data & sessions")
    print_status_line("Redis", "Connected", "success", "localhost:6379/db0 — LangGraph checkpointing")
    print_status_line("Ollama", "Ready", "success", "localhost:11434 — model: qwen3:4b")
    
    # Security
    print_security_info(
        rate_limit=30,
        burst_limit=50,
        jwt_configured=False,
        cors_origins=["http://localhost:3000", "http://localhost:8501"],
    )
    
    # Observability
    print_observability_info(
        langfuse_enabled=True,
        langfuse_url="http://localhost:3001",
        prometheus_enabled=True,
        log_level="INFO",
    )
    
    # Endpoints
    print_endpoints([
        ("API", "http://localhost:8000", "REST endpoints"),
        ("Swagger", "http://localhost:8000/docs", "Interactive API docs"),
        ("ReDoc", "http://localhost:8000/redoc", "Alternative API docs (clean)"),
        ("Chat UI", "http://localhost:8501", "Demo interface"),
        ("Langfuse", "http://localhost:3001", "LLM observability"),
    ])
    
    print_quick_links([
        ("Swagger", "http://localhost:8000/docs"),
        ("ReDoc", "http://localhost:8000/redoc"),
        ("Chat", "http://localhost:8501"),
        ("Traces", "http://localhost:3001"),
    ])
    
    print_startup_complete("Yonca AI API")
    
    # Demo tier comparison
    print()
    print(_c("  ═══════════════════════════════════════════════════════", Colors.BRIGHT_MAGENTA))
    print(_c("  DEMO: All Infrastructure Tiers", Colors.BRIGHT_MAGENTA))
    print_tier_comparison()
