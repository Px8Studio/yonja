# src/yonca/config.py
"""Application settings with environment variable support."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentMode(str, Enum):
    """Deployment mode enum.
    
    LOCAL: Local development with Ollama or Groq
    OPEN_SOURCE: Open-source models (Llama, Qwen, Mistral) via Groq or self-hosted
    CLOUD: Proprietary cloud models (Gemini, etc.)
    """

    LOCAL = "local"  # Local development mode
    OPEN_SOURCE = "open_source"  # Open-source models (fast with proper hardware)
    CLOUD = "cloud"  # Proprietary cloud models


class LLMProvider(str, Enum):
    """LLM provider enum.
    
    OLLAMA: Local LLM server (for offline/development)
    GROQ: Open-source models (Llama, Qwen, Mistral) with enterprise-grade performance
    GEMINI: Google's proprietary cloud models
    """

    OLLAMA = "ollama"  # Local LLM server
    GROQ = "groq"  # Open-source models, production-ready infrastructure
    GEMINI = "gemini"  # Proprietary cloud models


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="YONCA_",
        extra="ignore",  # Ignore extra fields in .env
    )

    # ===== Deployment =====
    deployment_mode: DeploymentMode = DeploymentMode.OPEN_SOURCE
    environment: str = "development"
    debug: bool = False

    # ===== API =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]

    # ===== LLM Provider =====
    llm_provider: LLMProvider = LLMProvider.GROQ

    # ===== Ollama (Local) =====
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    # ===== Open-Source Models (via Groq) =====
    # 2026 Gold Standard: Llama 4 Maverick - single model replaces entire stack
    # Demonstrates enterprise-ready performance with proper infrastructure
    # Can be self-hosted with appropriate hardware (LPU, GPU clusters)
    # Get free API key at: https://console.groq.com/
    groq_api_key: str | None = None
    groq_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"  # 2026 Gold Standard
    
    # Maverick Configuration:
    # - "meta-llama/llama-4-maverick-17b-128e-instruct": 2026 Gold Standard (ALL tasks)
    # 
    # Legacy Models (still supported):
    # - "llama-3.3-70b-versatile": Best for Azerbaijani language quality
    # - "qwen3-32b": Best for math/logic, calculations (Turkish leakage risk)
    # - "llama-3.1-8b-instant": Fastest open-source option
    # - "mixtral-8x7b-32768": Large context, good for complex queries

    # ===== Proprietary Cloud Models =====
    # Google Gemini - Closed-source cloud API
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

    # ===== Langfuse (Self-Hosted Observability) =====
    # Open-source LLM tracing - 100% data residency control
    # Dashboard: http://localhost:3001 (when running docker-compose)
    langfuse_enabled: bool = True
    langfuse_secret_key: str | None = None  # Get from Langfuse UI → Settings → API Keys
    langfuse_public_key: str | None = None  # Get from Langfuse UI → Settings → API Keys
    langfuse_host: str = "http://localhost:3001"  # Self-hosted instance
    langfuse_debug: bool = False  # Enable for trace debugging
    langfuse_sample_rate: float = 1.0  # 1.0 = trace 100% of requests

    # ===== App Metadata =====
    app_name: str = "Yonca AI"
    app_version: str = "0.1.0"

    # ===== Localization =====
    default_language: str = "az"

    @property
    def is_local(self) -> bool:
        """Check if running in local development mode."""
        return self.deployment_mode == DeploymentMode.LOCAL

    @property
    def is_open_source(self) -> bool:
        """Check if using open-source models."""
        return self.deployment_mode in (DeploymentMode.OPEN_SOURCE, DeploymentMode.LOCAL)

    @property
    def is_cloud(self) -> bool:
        """Check if using proprietary cloud models."""
        return self.deployment_mode == DeploymentMode.CLOUD

    @property
    def active_llm_model(self) -> str:
        """Get the active LLM model name based on provider."""
        if self.llm_provider == LLMProvider.OLLAMA:
            return self.ollama_model
        if self.llm_provider == LLMProvider.GROQ:
            return self.groq_model
        return self.gemini_model


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
