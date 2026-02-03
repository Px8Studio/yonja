# demo-ui/config.py
"""Configuration for the Chainlit demo UI.

HTTP-Only Architecture: All agent traffic goes through LangGraph Server.
Most settings are inherited from the main alim.config module.
This file only contains UI-specific settings.
"""

import os
from dataclasses import dataclass, field

# Import main settings for shared configuration
try:
    from alim.config import settings as alim_settings
except ImportError:
    alim_settings = None  # Graceful fallback during bootstrap


@dataclass
class DemoSettings:
    """Demo UI configuration settings.

    Inherits core settings from alim.config and adds UI-specific options.
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE SETTINGS (delegated to alim.config where possible)
    # ═══════════════════════════════════════════════════════════════════════════

    # LangGraph Server (HTTP-only architecture)
    langgraph_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_LANGGRAPH_BASE_URL",
            alim_settings.langgraph_base_url if alim_settings else "http://localhost:2024",
        )
    )
    langgraph_graph_id: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_LANGGRAPH_GRAPH_ID",
            alim_settings.langgraph_graph_id if alim_settings else "alim_agent",
        )
    )
    langgraph_required: bool = field(
        default_factory=lambda: os.getenv("ALIM_LANGGRAPH_REQUIRED", "false").lower()
        in ("true", "1", "yes")
    )

    # LLM settings (for display/status only - actual inference via LangGraph Server)
    llm_provider: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_LLM_PROVIDER",
            alim_settings.llm_provider.value if alim_settings else "ollama",
        )
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_OLLAMA_BASE_URL",
            alim_settings.ollama_base_url if alim_settings else "http://localhost:11434",
        )
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_OLLAMA_MODEL",
            alim_settings.ollama_model if alim_settings else "qwen3:4b",
        )
    )

    # Redis (for session caching)
    redis_url: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_REDIS_URL",
            alim_settings.redis_url if alim_settings else "redis://localhost:6379/0",
        )
    )

    # Database (shared with main API)
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "ALIM_DATABASE_URL",
            alim_settings.database_url
            if alim_settings
            else "postgresql+asyncpg://alim:alim_dev_password@localhost:5433/alim",
        )
    )

    # Chainlit-specific database URL (optional override)
    chainlit_database_url: str = field(
        default_factory=lambda: os.getenv("CHAINLIT_DATABASE_URL", "")
    )

    @property
    def effective_database_url(self) -> str:
        """Get the database URL for Chainlit data layer."""
        return self.chainlit_database_url or self.database_url

    @property
    def data_persistence_enabled(self) -> bool:
        """Check if data persistence is available (requires Postgres)."""
        db_url = self.effective_database_url
        return "postgresql" in db_url or "postgres" in db_url

    # API URL (for mobile-like client patterns)
    alim_api_url: str = field(
        default_factory=lambda: os.getenv("ALIM_API_URL", "http://localhost:8000")
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # OAUTH SETTINGS (UI-specific)
    # ═══════════════════════════════════════════════════════════════════════════

    oauth_google_client_id: str = field(
        default_factory=lambda: os.getenv("OAUTH_GOOGLE_CLIENT_ID", "")
    )
    oauth_google_client_secret: str = field(
        default_factory=lambda: os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    )

    @property
    def oauth_enabled(self) -> bool:
        """Check if OAuth is configured."""
        return bool(self.oauth_google_client_id and self.oauth_google_client_secret)

    # ═══════════════════════════════════════════════════════════════════════════
    # UI-SPECIFIC SETTINGS
    # ═══════════════════════════════════════════════════════════════════════════

    # Language & Session
    default_language: str = "az"
    session_timeout_seconds: int = 3600

    # Feature Flags
    enable_feedback: bool = field(
        default_factory=lambda: os.getenv("ENABLE_FEEDBACK", "true").lower() in ("true", "1", "yes")
    )
    enable_farm_selector: bool = field(
        default_factory=lambda: os.getenv("ENABLE_FARM_SELECTOR", "true").lower()
        in ("true", "1", "yes")
    )
    enable_weather_widget: bool = field(
        default_factory=lambda: os.getenv("ENABLE_WEATHER_WIDGET", "true").lower()
        in ("true", "1", "yes")
    )
    enable_thinking_steps: bool = field(
        default_factory=lambda: os.getenv("ENABLE_THINKING_STEPS", "true").lower()
        in ("true", "1", "yes")
    )
    enable_data_persistence: bool = field(
        default_factory=lambda: os.getenv("ENABLE_DATA_PERSISTENCE", "true").lower()
        in ("true", "1", "yes")
    )


# Global settings instance
settings = DemoSettings()
