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
    
    # Database (for farm context)
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            "sqlite+aiosqlite:///./data/yonca.db"
        )
    )
    
    # Demo settings
    default_language: str = "az"
    session_timeout_seconds: int = 3600
    
    # Feature flags
    enable_feedback: bool = True
    enable_farm_selector: bool = True
    enable_weather_widget: bool = True
    enable_thinking_steps: bool = True


# Global settings instance
settings = DemoSettings()
