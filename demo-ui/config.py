# demo-ui/config.py
"""Configuration for the Chainlit demo UI."""

import os
from dataclasses import dataclass, field


@dataclass
class DemoSettings:
    """Demo UI configuration settings."""
    
    # API connection (when using API client pattern)
    yonca_api_url: str = field(
        default_factory=lambda: os.getenv("YONCA_API_URL", "http://localhost:8000")
    )
    
    # LLM settings (when using direct integration)
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama")
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:4b")
    )
    
    # Redis for checkpointing
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    
    # Database for Chainlit data persistence (users, threads, settings)
    # Uses the SAME database as the main Yonca API
    # For Postgres: postgresql+asyncpg://user:pass@host:5432/yonca
    # For SQLite (dev only, no persistence): sqlite+aiosqlite:///./data/yonca.db
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            "sqlite+aiosqlite:///./data/yonca.db"
        )
    )
    
    # Chainlit-specific database URL (optional, defaults to DATABASE_URL)
    # Use this if Chainlit needs a separate connection string
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
    
    # OAuth settings (optional - for tracking real users in Langfuse)
    # Set these to enable Google login:
    #   OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
    #   OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
    #   CHAINLIT_AUTH_SECRET=any-random-secret-string
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
    
    # Demo settings
    default_language: str = "az"
    session_timeout_seconds: int = 3600
    
    # Integration mode: "direct" (LangGraph) or "api" (FastAPI bridge)
    # Use "api" mode to demo the exact API contract Digital Umbrella will use
    integration_mode: str = field(
        default_factory=lambda: os.getenv("INTEGRATION_MODE", "direct")
    )
    
    @property
    def use_api_bridge(self) -> bool:
        """Check if using API bridge mode."""
        return self.integration_mode.lower() == "api"
    
    # Feature flags
    enable_feedback: bool = True
    enable_farm_selector: bool = True
    enable_weather_widget: bool = True
    enable_thinking_steps: bool = True
    enable_data_persistence: bool = True  # Enable Chainlit data layer


# Global settings instance
settings = DemoSettings()
