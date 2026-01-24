# src/ALİM/config.py
"""Application settings with environment variable support."""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================
# Environment Configuration (Two-Axis Model)
# ============================================================
# Axis 1: Environment — WHAT stage of development
# Axis 2: InfrastructureMode — WHERE it runs
# Axis 3: LLMProvider — WHICH LLM backend (already exists below)
# ============================================================


class Environment(str, Enum):
    """Application environment — WHAT stage of development.

    DEVELOPMENT: Local development with debug enabled, relaxed security
    STAGING: Pre-production testing with production-like config
    PRODUCTION: Production deployment with full security, optimized settings
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class InfrastructureMode(str, Enum):
    """Infrastructure mode — WHERE the application runs.

    LOCAL: Running on developer laptop (Docker Desktop, podman, etc.)
    CLOUD: Running in cloud infrastructure (Render, Railway, K8s, etc.)
    """

    LOCAL = "local"  # Developer laptop, local Docker
    CLOUD = "cloud"  # Cloud infrastructure (Render, Railway, K8s)


class DeploymentMode(str, Enum):
    """DEPRECATED: Use Environment + InfrastructureMode instead.

    Kept for backwards compatibility. Will be removed in future version.

    Migration guide:
    - LOCAL → Environment.DEVELOPMENT + InfrastructureMode.LOCAL
    - OPEN_SOURCE → Environment.STAGING + LLMProvider.GROQ
    - CLOUD → Environment.PRODUCTION + InfrastructureMode.CLOUD
    """

    LOCAL = "local"  # DEPRECATED: Use Environment.DEVELOPMENT
    OPEN_SOURCE = "open_source"  # DEPRECATED: Use LLMProvider.GROQ
    CLOUD = "cloud"  # DEPRECATED: Use InfrastructureMode.CLOUD


class LLMProvider(str, Enum):
    """LLM provider enum.

    OLLAMA: Local LLM server (for offline/development)
    GROQ: Open-source models (Llama, Qwen, Mistral) with enterprise-grade performance
    """

    OLLAMA = "ollama"  # Local LLM server
    GROQ = "groq"  # Open-source models, production-ready infrastructure
    VLLM = "vllm"  # Self-hosted OpenAI-compatible (AzInTelecom/DigiRella)


class InferenceTier(str, Enum):
    """ALİM Infrastructure Matrix — Inference deployment tiers.

    From ALİM (Azərbaycan LLM Ekosistem Matrisi):
    - Tier I: Groq LPU (cloud benchmark — proves what's possible)
    - Tier III: DigiRella Cloud (rented GPU from AzInTelecom)
    - Tier IV: DigiRella Owned (self-hosted hardware)

    DigiRella = "Digital Farm Relay" — brand for self-hosted LLM infrastructure.
    Groq benchmarks (200-300 tok/s) achievable with DigiRella hardware.
    """

    TIER_I_GROQ = "tier_i_groq"  # Groq LPU — Cloud Benchmark
    TIER_III_SOVEREIGN = "tier_iii_sov"  # DigiRella Cloud — Rented GPU
    TIER_IV_ONPREM = "tier_iv_onprem"  # DigiRella Owned — Self-Hosted


# ALİM Infrastructure Matrix — Tier specifications
INFERENCE_TIER_SPECS = {
    InferenceTier.TIER_I_GROQ: {
        "name": "Tier I: Groq LPU",
        "tagline": "Cloud Benchmark (Open-Source Models)",
        "provider": "Groq Cloud (LPU infrastructure)",
        "models": ["Llama 4 Maverick 17B", "Qwen 3 32B", "Llama 3.3 70B"],
        "latency": "~200ms (P95)",
        "throughput": "800 tok/s (benchmark target)",
        "data_residency": "US (Groq servers)",
        "cost_range": "$0–50/mo (dev)",
        "use_case": "Development, testing, benchmarking",
        "icon": "⚡",
        "self_hosted_equivalent": "DigiRella Standard ($6,300) or Pro ($145k)",
        "notes": "Proves performance achievable with open-source + optimized hardware. "
        "Same models/performance available with DigiRella self-hosted.",
    },
    InferenceTier.TIER_III_SOVEREIGN: {
        "name": "Tier III: DigiRella Cloud",
        "tagline": "Sovereign Rented GPU (AzInTelecom)",
        "provider": "AzInTelecom (DigiRella Cloud partner)",
        "models": ["Llama 3.3 70B", "Qwen 3 32B", "Mistral Large"],
        "latency": "~600ms (P95) → target: ~250ms",
        "throughput": "80 tok/s → target: 200+ tok/s (Groq-equivalent)",
        "data_residency": "Azerbaijan 🇦🇿 (Baku DC)",
        "cost_range": "$800–1,500/mo (rented GPU)",
        "use_case": "Government, regulated industries, data sovereignty",
        "icon": "🏛️",
        "groq_equivalent": "Groq Tier I performance + Azerbaijan data residency",
        "notes": "Rented GPU capacity from AzInTelecom. Same open-source models as Groq. "
        "Performance target: match Groq benchmarks with local sovereignty.",
    },
    InferenceTier.TIER_IV_ONPREM: {
        "name": "Tier IV: DigiRella Owned",
        "tagline": "Self-Hosted Hardware (Your Premises)",
        "provider": "Self-hosted (DigiRella hardware profiles)",
        "models": ["ALL Groq models (Llama 70B, Qwen 32B, Maverick 17B, etc.)"],
        "latency": "~250ms (P95) — Groq-equivalent",
        "throughput": "200-300 tok/s — Groq-equivalent",
        "data_residency": "Customer premises (air-gapped capable)",
        "cost_range": "$2,600–145,000 one-time (see DigiRella profiles)",
        "use_case": "Offline farms, military, banks, air-gapped networks",
        "icon": "🔒",
        "groq_equivalent": "Full Groq performance, your hardware",
        "profiles": {
            "lite": "1× RTX 4090 ($2,600) → 300+ tok/s (8B models)",
            "standard": "2× RTX 5090 ($6,300) → 200+ tok/s (70B models)",
            "pro": "8× A100 ($145k) → 300+ tok/s (all models, Groq-level)",
        },
        "notes": "Owned hardware with Groq-equivalent performance. No recurring costs. "
        "Complete data isolation. Fine-tuning capable.",
    },
}


class AgentMode(str, Enum):
    """ALİM Agent Modes — Dynamic Model Handling Strategies.

    FAST: Speed-optimized (Smaller models, lower latency)
    THINKING: Reasoning-optimized (CoT enabled / specific logic models)
    AGENT: Full autonomy + tools/connectors (highest fidelity)
    """

    FAST = "fast"
    THINKING = "thinking"
    AGENT = "agent"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="ALIM_",
        extra="ignore",  # Ignore extra fields in .env
    )

    # ===== Deployment =====
    # New two-axis model: Environment (stage) + InfrastructureMode (where)
    environment: Environment = Environment.DEVELOPMENT
    infrastructure_mode: InfrastructureMode = InfrastructureMode.LOCAL
    debug: bool = False

    # DEPRECATED: Use environment + infrastructure_mode instead
    deployment_mode: DeploymentMode = DeploymentMode.OPEN_SOURCE

    # ===== LangGraph Server =====
    # When True, LangGraph Dev Server is required (HTTP mode only)
    # When False, allows fallback to in-process execution (direct mode)
    langgraph_required: bool = True

    # ===== API =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]

    # ===== LLM Provider =====
    llm_provider: LLMProvider = LLMProvider.OLLAMA  # Explicit default instead of relying on env

    # ===== Ollama (Local) =====
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    # ===== Self-Hosted vLLM (AzInTelecom/DigiRella) =====
    # OpenAI-compatible HTTP endpoint for sovereign deployments
    vllm_base_url: str | None = None  # e.g., "http://vllm:8000/v1"
    vllm_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"

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

    # ===== Database =====
    database_url: str = (
        "postgresql+asyncpg://alim:alim_dev_password@localhost:5433/alim"
    )  # pragma: allowlist secret
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ===== Redis =====
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # ===== LangGraph Dev Server =====
    # HTTP endpoint for decoupled graph execution (async/scalable)
    # Dev server runs graph in separate process - critical for multi-user concurrency
    langgraph_base_url: str = "http://127.0.0.1:2024"
    langgraph_graph_id: str = "ALİM_agent"  # From langgraph.json

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
    app_name: str = "ALİM"
    app_version: str = "0.1.0"

    # ===== Localization =====
    default_language: str = "az"

    # ===== New Two-Axis Properties =====
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == Environment.STAGING

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_local_infra(self) -> bool:
        """Check if running on local infrastructure (Docker Desktop, etc.)."""
        return self.infrastructure_mode == InfrastructureMode.LOCAL

    @property
    def is_cloud_infra(self) -> bool:
        """Check if running on cloud infrastructure (Render, K8s, etc.)."""
        return self.infrastructure_mode == InfrastructureMode.CLOUD

    # ===== Legacy Properties (DEPRECATED) =====
    @property
    def is_local(self) -> bool:
        """DEPRECATED: Use is_local_infra instead."""
        return self.deployment_mode == DeploymentMode.LOCAL

    @property
    def is_open_source(self) -> bool:
        """DEPRECATED: Check llm_provider instead."""
        return self.deployment_mode in (DeploymentMode.OPEN_SOURCE, DeploymentMode.LOCAL)

    @property
    def is_cloud(self) -> bool:
        """DEPRECATED: Use is_cloud_infra instead."""
        return self.deployment_mode == DeploymentMode.CLOUD

    @property
    def active_llm_model(self) -> str:
        """Get the active LLM model name based on provider."""
        if self.llm_provider == LLMProvider.OLLAMA:
            return self.ollama_model
        if self.llm_provider == LLMProvider.GROQ:
            return self.groq_model
        if self.llm_provider == LLMProvider.VLLM:
            return self.vllm_model
        return self.groq_model  # Default to Groq

    @property
    def inference_tier(self) -> "InferenceTier":
        """Get the current ALİM infrastructure tier based on provider."""
        if self.llm_provider == LLMProvider.OLLAMA:
            return InferenceTier.TIER_IV_ONPREM
        if self.llm_provider == LLMProvider.GROQ:
            return InferenceTier.TIER_I_GROQ
        if self.llm_provider == LLMProvider.VLLM:
            return InferenceTier.TIER_III_SOVEREIGN
        return InferenceTier.TIER_I_GROQ  # Default

    @property
    def inference_tier_spec(self) -> dict:
        """Get the full specification for the current inference tier."""
        return INFERENCE_TIER_SPECS.get(self.inference_tier, {})

    def get_model_for_mode(self, mode: AgentMode) -> str:
        """Get the specific model to use for a requested AgentMode.

        Dynamic selection based on available models in the current Tier.
        """
        # Default fallback models
        fast_model = "qwen3:4b"
        thinking_model = "qwen3:32b"  # or specialized CoT model
        agent_model = "llama-3.3-70b-versatile"

        # Tier-specific overrides could go here
        if self.llm_provider == LLMProvider.GROQ:
            fast_model = "llama-3.1-8b-instant"
            thinking_model = "llama-3.3-70b-versatile"  # approx for now
            agent_model = "llama-3.3-70b-versatile"

        # Override with specific config variables if set (future proofing)
        # ...

        if mode == AgentMode.FAST:
            return fast_model
        elif mode == AgentMode.THINKING:
            return thinking_model
        elif mode == AgentMode.AGENT:
            return agent_model

        return fast_model  # Fallback


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
