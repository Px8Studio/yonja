# src/yonca/config.py
"""Application settings with environment variable support."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentMode(str, Enum):
    """Deployment mode enum."""

    LOCAL = "local"
    CLOUD = "cloud"


class LLMProvider(str, Enum):
    """LLM provider enum."""

    OLLAMA = "ollama"
    GEMINI = "gemini"
    GROQ = "groq"  # Ultra-fast cloud inference


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="YONCA_",
    )

    # ===== Deployment =====
    deployment_mode: DeploymentMode = DeploymentMode.LOCAL
    environment: str = "development"
    debug: bool = False

    # ===== API =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]

    # ===== LLM Provider =====
    llm_provider: LLMProvider = LLMProvider.OLLAMA

    # Ollama (Local) - Slow on CPU, fast with GPU
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"  # Can also use: atllama, qwen3:1.7b

    # Groq (Cloud) - Ultra-fast LPU hardware, FREE tier!
    # Get key at: https://console.groq.com/
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"  # Best for Azerbaijani (prev: llama-3.1-8b-instant)

    # Gemini (Cloud) - Google's fast cloud API
    # Get key at: https://ai.google.dev/
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"

    # ===== Database =====
    database_url: str = "sqlite+aiosqlite:///./data/yonca.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ===== Redis =====
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # ===== Security =====
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # ===== Rate Limiting =====
    rate_limit_requests_per_minute: int = 30
    rate_limit_burst: int = 50

    # ===== Observability =====
    log_level: str = "INFO"
    log_format: str = "json"
    prometheus_enabled: bool = True

    # ===== App Metadata =====
    app_name: str = "Yonca AI"
    app_version: str = "0.1.0"

    # ===== Localization =====
    default_language: str = "az"

    @property
    def is_local(self) -> bool:
        """Check if running in local mode."""
        return self.deployment_mode == DeploymentMode.LOCAL

    @property
    def is_cloud(self) -> bool:
        """Check if running in cloud mode."""
        return self.deployment_mode == DeploymentMode.CLOUD

    @property
    def active_llm_model(self) -> str:
        """Get the active LLM model name based on provider."""
        if self.llm_provider == LLMProvider.OLLAMA:
            return self.ollama_model
        return self.gemini_model


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
