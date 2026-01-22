# demo-ui/app.py
# =========================================================================
# BRAND IDENTITY & IP PROTECTION NOTICE (ZekaLab)
# -------------------------------------------------------------------------
# AGENT NAME: ALEM (Agronomical Logic & Evaluation Model)
# SUBTITLE:   ALEM | Aqronom Assistentiniz
# DEVELOPER:  ZekaLab (Response to DigiRella Call)
#
# INSTRUCTION: The term "Sidecar" is strictly prohibited in the UI,
# documentation, and user-facing logs. ALEM is a standalone proprietary
# service layer. All UI elements must reflect ALEM branding.
#
# USER-FACING BRAND: ALEM (not "Yonca AI")
# INTERNAL PROJECT: Yonca (codebase/technical references only)
# =========================================================================
"""ALEM Demo — Chainlit Application.

This is the main Chainlit application that provides a demo UI
for ALEM (Agronomical Logic & Evaluation Model) using native LangGraph integration.

Usage:
    chainlit run app.py -w --port 8501

The app uses Chainlit's native LangGraph callback handler for:
- Automatic step visualization (shows which node is executing)
- Token streaming (real-time response display)
- Session persistence (conversation survives refresh)

Authentication (Optional):
- Supports Google OAuth for tracking real users in Langfuse
- Set OAUTH_GOOGLE_CLIENT_ID and OAUTH_GOOGLE_CLIENT_SECRET to enable
- Real user identity is separate from synthetic farmer profiles
"""

# MUST be first - fix engineio packet limit before ANY chainlit imports
import engineio

engineio.payload.Payload.max_decode_packets = 500

import json  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Load .env files BEFORE any other imports
from dotenv import load_dotenv  # noqa: E402

demo_ui_dir = Path(__file__).parent
project_root = demo_ui_dir.parent
load_dotenv(project_root / ".env")
load_dotenv(demo_ui_dir / ".env")

sys.path.insert(0, str(project_root / "src"))

# ============================================
# CHAINLIT DATA LAYER INITIALIZATION (CRITICAL)
# ============================================
# Must happen BEFORE importing chainlit to prevent "storage client not initialized" warning
import asyncio  # noqa: E402
import logging  # noqa: E402

from chainlit.data.chainlit_data_layer import ChainlitDataLayer  # noqa: E402
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer  # noqa: E402
from fastapi import APIRouter, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

logger = logging.getLogger(__name__)


async def init_chainlit_data_layer():
    """Initialize Chainlit's SQLAlchemy data layer with async engine."""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/yonca.db")
        logger.info(
            f"Initializing Chainlit data layer with: {db_url.split('@')[-1] if '@' in db_url else db_url}"
        )

        # Create async engine
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # Create async session factory
        sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Initialize Chainlit data layer
        # Note: Newer Chainlit versions expect only conninfo string, not engine
        data_layer = SQLAlchemyDataLayer(
            conninfo=db_url,
        )

        # Set as global data layer
        ChainlitDataLayer._instance = data_layer

        logger.info("✅ Chainlit data layer initialized successfully")
        return data_layer
    except Exception as e:
        logger.warning(f"⚠️  Chainlit data layer initialization failed: {e}")
        logger.warning("   Threads will not be persisted (sessions will be stateless)")
        return None


# Initialize data layer before importing chainlit (but only if Postgres is configured)
# This must happen BEFORE @cl.data_layer decorator runs
_data_layer_initialized = False
try:
    from config import settings as demo_settings_early

    if demo_settings_early.data_persistence_enabled:
        asyncio.run(init_chainlit_data_layer())
        _data_layer_initialized = True
        logger.info("✅ Data layer pre-initialized for Chainlit registration")
    else:
        logger.info("⏩ Skipping data layer init (SQLite/no Postgres configured)")
except Exception as e:
    logger.error(f"Failed to initialize data layer: {e}")
    _data_layer_initialized = False

# Now safe to import chainlit  # noqa: E402
import chainlit as cl  # noqa: E402
import structlog  # noqa: E402
from alem_persona import ALEMPersona, PersonaProvisioner  # noqa: E402
from alem_persona_db import (  # noqa: E402
    load_alem_persona_from_db,
    save_alem_persona_to_db,
    update_persona_login_time,
)
from chainlit.input_widget import MultiSelect, NumberInput, Select, Switch  # noqa: E402
from chainlit.types import ThreadDict  # noqa: E402
from components.insights_dashboard import (  # noqa: E402
    render_dashboard_sidebar,
)
from components.spinners import (  # noqa: E402
    LoadingStates,
)

# Import demo-ui config and API client  # noqa: E402
from config import settings as demo_settings  # noqa: E402
from data_layer import (  # noqa: E402
    get_data_layer,
    load_user_settings,
    save_farm_scenario,
    save_user_settings,
)
from langchain_core.runnables import RunnableConfig  # noqa: E402

# Import insights dashboard components  # noqa: E402
from services.langfuse_insights import (  # noqa: E402
    get_insights_client,
    get_user_dashboard_data,
)
from services.yonca_client import YoncaClient  # noqa: E402

# Import from main yonca package (for direct mode)  # noqa: E402
from yonca.agent.graph import compile_agent_graph  # noqa: E402
from yonca.agent.memory import get_checkpointer_async  # noqa: E402
from yonca.observability.banner import (  # noqa: E402
    print_endpoints,
    print_infrastructure_tier,
    print_llm_info,
    print_model_capabilities,
    print_quick_links,
    print_section_header,
    print_startup_banner,
    print_startup_complete,
    print_status_line,
)

logger = structlog.get_logger()

# ============================================
# STARTUP BANNER
# ============================================
print_startup_banner("demo-ui", "1.0.0", "development")

# ─────────────────────────────────────────────────────────────
# Integration Mode
# ─────────────────────────────────────────────────────────────
print_section_header("⚙️  Integration Mode")

mode_details = {
    "direct": ("🔗 Direct LangGraph", "Agent runs in-process, best for development"),
    "api": ("🌐 API Bridge", "Calls FastAPI backend, mirrors production"),
}
mode_name, mode_desc = mode_details.get(demo_settings.integration_mode, ("Unknown", ""))
print_status_line("Mode", mode_name, "success")
print_status_line("Description", mode_desc, "info")

# ─────────────────────────────────────────────────────────────
# LLM Configuration
# ─────────────────────────────────────────────────────────────
if demo_settings.integration_mode == "direct":
    # Direct mode uses Ollama or configured provider
    provider_map = {
        "ollama": ("Ollama (Local)", demo_settings.ollama_base_url),
        "groq": ("Groq (Cloud)", "https://api.groq.com/openai/v1"),
    }
    provider_name, base_url = provider_map.get(
        demo_settings.llm_provider, (demo_settings.llm_provider, "")
    )

    print_llm_info(
        provider=provider_name,
        model=demo_settings.ollama_model,
        mode="local" if demo_settings.llm_provider == "ollama" else "open_source",
        base_url=base_url,
        api_key_set=demo_settings.llm_provider == "ollama",  # Ollama doesn't need key
    )
    print_model_capabilities(demo_settings.ollama_model)

    # Show ALEM Infrastructure Tier
    try:
        from yonca.config import settings as yonca_settings

        print_infrastructure_tier(yonca_settings.inference_tier_spec)
    except Exception:
        pass  # Skip if config not available
else:
    print_section_header("🤖 LLM Configuration")
    print_status_line("Provider", "Via API Bridge", "info")
    print_status_line("Endpoint", demo_settings.yonca_api_url, "info")

# ─────────────────────────────────────────────────────────────
# Data Layer
# ─────────────────────────────────────────────────────────────
print_section_header("🗄️  Data Layer")

redis_host = (
    demo_settings.redis_url.replace("redis://", "").split("/")[0]
    if demo_settings.redis_url
    else "not configured"
)
redis_db = demo_settings.redis_url.split("/")[-1] if "/" in demo_settings.redis_url else "0"
print_status_line(
    "Redis",
    f"localhost:{redis_host.split(':')[-1]}/db{redis_db}",
    "success",
    "LangGraph checkpointing",
)

if demo_settings.data_persistence_enabled:
    db_host = (
        demo_settings.effective_database_url.split("@")[-1].split("/")[0]
        if "@" in demo_settings.effective_database_url
        else "local"
    )
    db_name = (
        demo_settings.effective_database_url.split("/")[-1].split("?")[0]
        if "/" in demo_settings.effective_database_url
        else "yonca"
    )
    print_status_line("PostgreSQL", f"{db_host}/{db_name}", "success", "users, threads, settings")
else:
    print_status_line("PostgreSQL", "Not configured", "warning", "sessions not persisted")

# ─────────────────────────────────────────────────────────────
# Features
# ─────────────────────────────────────────────────────────────
print_section_header("✨ Features")
print_status_line(
    "OAuth",
    "Enabled" if demo_settings.oauth_enabled else "Disabled",
    "success" if demo_settings.oauth_enabled else "info",
    "Google login" if demo_settings.oauth_enabled else "anonymous mode",
)
print_status_line(
    "Farm Selector",
    "Enabled" if demo_settings.enable_farm_selector else "Disabled",
    "success" if demo_settings.enable_farm_selector else "info",
)
print_status_line(
    "Thinking Steps",
    "Enabled" if demo_settings.enable_thinking_steps else "Disabled",
    "success" if demo_settings.enable_thinking_steps else "info",
    "shows agent reasoning",
)
print_status_line(
    "Feedback",
    "Enabled" if demo_settings.enable_feedback else "Disabled",
    "success" if demo_settings.enable_feedback else "info",
    "👍/👎 buttons",
)

# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────
print_endpoints(
    [
        ("Chat UI", "http://localhost:8501", "Interactive Chainlit demo"),
        ("Swagger", "http://localhost:8000/docs", "Interactive API docs"),
        ("ReDoc", "http://localhost:8000/redoc", "Clean API reference"),
        ("Health", "http://localhost:8000/health", "Readiness & liveness probes"),
        ("Langfuse UI", "http://localhost:3001", "LLM tracing & analytics dashboard"),
        ("Langfuse API", "http://localhost:3001/api/public", "Langfuse Public API"),
        ("LangGraph API", "http://127.0.0.1:2024", "LangGraph development server"),
        ("LangGraph Docs", "http://127.0.0.1:2024/docs", "LangGraph API documentation"),
    ]
)

print_quick_links(
    [
        ("Chat", "http://localhost:8501"),
        ("Swagger", "http://localhost:8000/docs"),
        ("ReDoc", "http://localhost:8000/redoc"),
        ("Traces", "http://localhost:3001/traces"),
        ("LangGraph", "http://127.0.0.1:2024"),
        ("Studio", "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"),
    ]
)

print_startup_complete("🌿 Yonca Demo UI")

# ============================================
# DATA PERSISTENCE (Chainlit Data Layer)
# ============================================
# This enables:
# - User persistence (OAuth users stored in Postgres)
# - Thread/conversation history
# - ChatSettings persistence across sessions
#
# Requires Postgres database. SQLite falls back to session-only storage.
# Set DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/yonca
# ============================================
if demo_settings.data_persistence_enabled:
    # Register data layer with Chainlit when Postgres is available
    @cl.data_layer
    def _get_data_layer():
        """Register Chainlit data layer for persistence.

        This decorator tells Chainlit to use our SQLAlchemy data layer
        for persisting users, threads, and settings.

        Only registered when Postgres is configured (data_persistence_enabled=True).
        SQLite falls back to session-only storage.
        """
        return get_data_layer()


# Global checkpointer (initialized once in async context) - for direct mode
_checkpointer = None

# Global API client (for API bridge mode)
_api_client: YoncaClient | None = None

# ============================================
# LLM MODEL PROFILES (for Chat Profile dropdown)
# ============================================
# Available models are pulled from Ollama container.
# Add new models with: docker exec yonca-ollama ollama pull <model>
#
# This dictionary is used by:
# 1. @cl.set_chat_profiles - to show available models in header dropdown
# 2. resolve_active_model() - to validate selected model
#
# Runtime model switching is now fully implemented:
# - Selected model flows through RunnableConfig metadata
# - Agent nodes use get_llm_from_config() to respect the selection
# - See: src/yonca/llm/factory.py - get_llm_from_config()
# ============================================
LLM_MODEL_PROFILES = {
    "qwen3:4b": {
        "name": "Qwen3 4B",
        "description": "**Qwen3 4B** — Sürətli və yüngül model. Sadə suallar üçün ideal.",
        "icon": "🚀",
        "speed": "fast",
    },
    "atllama:latest": {
        "name": "ATLlama",
        "description": "**ATLlama** — Azərbaycan dili üçün optimallaşdırılmış model.",
        "icon": "🇦🇿",
        "speed": "medium",
    },
    "llama3.2:3b": {
        "name": "Llama 3.2 3B",
        "description": "**Llama 3.2 3B** — Meta-nın ən son yüngül modeli.",
        "icon": "🦙",
        "speed": "fast",
    },
    "mistral:7b": {
        "name": "Mistral 7B",
        "description": "**Mistral 7B** — Güclü və səmərəli model. Ətraflı cavablar üçün.",
        "icon": "🌪️",
        "speed": "medium",
    },
    "gemma2:9b": {
        "name": "Gemma 2 9B",
        "description": "**Gemma 2 9B** — Google-un açıq mənbəli modeli. Yüksək keyfiyyət.",
        "icon": "💎",
        "speed": "slow",
    },
}


def resolve_active_model() -> dict:
    """Return a single source of truth for the active model metadata.

    Checks for model selection from:
    1. Chat Profile (header dropdown - now used for LLM selection)
    2. Chat Settings (sidebar settings panel)
    3. Default from config
    """
    integration_mode = demo_settings.integration_mode.lower()
    provider = demo_settings.llm_provider.lower()

    if integration_mode == "api":
        return {
            "provider": "yonca-api",
            "model": "server_default",
            "location": "cloud",
            "integration_mode": "api",
            "source": "fastapi",
        }

    # Get model from chat profile (header dropdown) or settings
    selected_model = None
    try:
        # Chat Profile is now the LLM model name (e.g., "qwen3:4b")
        chat_profile = cl.user_session.get("chat_profile")
        if chat_profile and chat_profile in LLM_MODEL_PROFILES:
            selected_model = chat_profile

        # Fallback to settings panel selection
        if not selected_model:
            settings = cl.user_session.get("chat_settings") or {}
            selected_model = settings.get("llm_model") if isinstance(settings, dict) else None
    except Exception:
        pass  # Session not available yet

    # Final fallback to config default
    model = selected_model or demo_settings.ollama_model

    location = "local" if provider == "ollama" else "cloud"
    base_url = (
        demo_settings.ollama_base_url if provider == "ollama" else "https://api.groq.com/openai/v1"
    )

    return {
        "provider": provider,
        "model": model,
        "location": location,
        "integration_mode": integration_mode,
        "source": "langgraph",
        "base_url": base_url,
    }


async def get_app_checkpointer():
    """Get or create the checkpointer singleton (async) - for direct mode.

    Priority: PostgreSQL (persistent) > Redis (fast) > Memory (dev only)
    """
    global _checkpointer
    if _checkpointer is None:
        # Prefer Postgres for persistence, fallback to Redis, then Memory
        # This ensures conversation history survives restarts
        _checkpointer = await get_checkpointer_async(
            redis_url=demo_settings.redis_url,
            postgres_url=demo_settings.database_url,
            backend="auto",  # Will try Postgres first if available
        )
    return _checkpointer


async def get_api_client() -> YoncaClient:
    """Get or create the API client singleton - for API bridge mode."""
    global _api_client
    if _api_client is None:
        _api_client = YoncaClient(base_url=demo_settings.yonca_api_url)
        await _api_client.__aenter__()
        logger.info("api_client_connected", base_url=demo_settings.yonca_api_url)
    return _api_client


# ============================================
# STARTERS (Quick Action Suggestions)
# ============================================
# These appear on the welcome screen to help users start conversations.

# ============================================
# CHAT PROFILES (Farmer Personas)
# ============================================
# Different profiles for different farming needs.
# Each profile has specialized starters and system prompts.

# ============================================
# EXPERTISE AREAS — Smart Multi-Select System
# ============================================
# Maps user's crop types to relevant expertise areas.
# Used to auto-configure chat settings based on ALEM persona.

# Expertise area definitions with Azerbaijani labels
EXPERTISE_AREAS = {
    "general": "Ümumi kənd təsərrüfatı",
    "cotton": "Pambıqçılıq",
    "wheat": "Taxılçılıq (buğda, arpa)",
    "orchard": "Meyvəçilik (alma, üzüm)",
    "vegetable": "Tərəvəzçilik",
    "livestock": "Heyvandarlıq",
    "advanced": "Qabaqcıl texnologiyalar",
}

# Map crop types (from ALEM persona) to expertise areas
CROP_TO_EXPERTISE = {
    # Industrial crops
    "Pambıq": ["cotton"],
    "Cotton": ["cotton"],
    # Grains
    "Buğda": ["wheat"],
    "Wheat": ["wheat"],
    "Arpa": ["wheat"],
    "Barley": ["wheat"],
    "Qarğıdalı": ["wheat"],  # Corn grouped with grains
    "Corn": ["wheat"],
    # Fruits/Orchards
    "Alma": ["orchard"],
    "Apple": ["orchard"],
    "Üzüm": ["orchard"],
    "Grape": ["orchard"],
    "Fındıq": ["orchard"],
    "Hazelnut": ["orchard"],
    "Nar": ["orchard"],
    "Pomegranate": ["orchard"],
    "Şaftalı": ["orchard"],
    "Peach": ["orchard"],
    # Vegetables
    "Pomidor": ["vegetable"],
    "Tomato": ["vegetable"],
    "Xıyar": ["vegetable"],
    "Cucumber": ["vegetable"],
    "Bibər": ["vegetable"],
    "Pepper": ["vegetable"],
    "Kartof": ["vegetable"],
    "Potato": ["vegetable"],
    # Specialty
    "Çay": ["vegetable"],  # Tea grouped with vegetables for now
    "Tea": ["vegetable"],
    "Sitrus": ["orchard"],
    "Citrus": ["orchard"],
}

# Map experience level to add advanced expertise
EXPERIENCE_TO_EXPERTISE = {
    "expert": ["advanced"],
    "intermediate": [],
    "novice": [],
}


def detect_expertise_from_persona(persona_dict: dict | None) -> list[str]:
    """Detect relevant expertise areas from ALEM persona.

    Uses crop type and experience level to determine smart defaults.

    Args:
        persona_dict: ALEM persona dictionary with crop_type, experience_level

    Returns:
        List of expertise area IDs (e.g., ["cotton", "advanced"])
    """
    if not persona_dict:
        return ["general"]

    expertise = set()

    # Add expertise based on crop type
    crop_type = persona_dict.get("crop_type", "")
    if crop_type in CROP_TO_EXPERTISE:
        expertise.update(CROP_TO_EXPERTISE[crop_type])

    # Add expertise based on experience level
    experience = persona_dict.get("experience_level", "intermediate")
    if experience in EXPERIENCE_TO_EXPERTISE:
        expertise.update(EXPERIENCE_TO_EXPERTISE[experience])

    # Always include general if nothing specific detected
    if not expertise:
        expertise.add("general")

    # Sort for consistent ordering
    return sorted(list(expertise))


# Profile-specific starters
PROFILE_STARTERS = {
    "general": [
        cl.Starter(
            label="📅 Həftəlik plan",
            message="Bu həftə üçün iş planı hazırla",
            icon="/public/elements/calendar.svg",
        ),
        cl.Starter(
            label="🌤️ Hava proqnozu",
            message="Bu günkü hava proqnozu necədir?",
            icon="/public/elements/weather.svg",
        ),
        cl.Starter(
            label="💧 Suvarma vaxtı",
            message="Sahəmi nə vaxt suvarmalıyam?",
            icon="/public/elements/water.svg",
        ),
        cl.Starter(
            label="💰 Subsidiyalar",
            message="Hansı subsidiyalardan yararlana bilərəm?",
            icon="/public/elements/money.svg",
        ),
    ],
    "cotton": [
        cl.Starter(
            label="🌱 Pambıq əkini",
            message="Pambıq əkini üçün ən yaxşı vaxt nədir?",
            icon="/public/elements/plant.svg",
        ),
        cl.Starter(
            label="🐛 Pambıq zərərvericisi",
            message="Pambıqda hansı zərərvericilər var?",
            icon="/public/elements/bug.svg",
        ),
        cl.Starter(
            label="💧 Pambıq suvarması",
            message="Pambıq üçün suvarma norması nə qədərdir?",
            icon="/public/elements/water.svg",
        ),
        cl.Starter(
            label="🧪 Pambıq gübrəsi",
            message="Pambıq üçün hansı gübrələr lazımdır?",
            icon="/public/elements/fertilizer.svg",
        ),
    ],
    "wheat": [
        cl.Starter(
            label="🌾 Buğda əkini",
            message="Payızlıq buğda nə vaxt əkilir?",
            icon="/public/elements/wheat.svg",
        ),
        cl.Starter(
            label="🌡️ Don zədəsi",
            message="Buğdanı dondan necə qorumaq olar?",
            icon="/public/elements/frost.svg",
        ),
        cl.Starter(
            label="🌿 Alaq otları",
            message="Buğdada alaq otlarına qarşı nə etmək olar?",
            icon="/public/elements/weed.svg",
        ),
        cl.Starter(
            label="📊 Buğda məhsuldarlığı",
            message="Buğda məhsuldarlığını necə artırmaq olar?",
            icon="/public/elements/chart.svg",
        ),
    ],
    "orchard": [
        cl.Starter(
            label="🍎 Alma bağı",
            message="Alma ağaclarının qulluğu necə olmalıdır?",
            icon="/public/elements/apple.svg",
        ),
        cl.Starter(
            label="🍇 Üzüm bağı",
            message="Üzüm bağının budaması nə vaxt olmalıdır?",
            icon="/public/elements/grape.svg",
        ),
        cl.Starter(
            label="🌸 Çiçəklənmə",
            message="Meyvə ağaclarının çiçəklənmə dövrü nə vaxtdır?",
            icon="/public/elements/flower.svg",
        ),
        cl.Starter(
            label="🪲 Meyvə zərərvericisi",
            message="Meyvə ağaclarında hansı zərərvericilər var?",
            icon="/public/elements/bug.svg",
        ),
    ],
    "vegetable": [
        cl.Starter(
            label="🍅 Pomidor əkini",
            message="Pomidor əkini üçün torpaq necə hazırlanır?",
            icon="/public/elements/tomato.svg",
        ),
        cl.Starter(
            label="🥒 Xıyar becərilməsi",
            message="Xıyar becərilməsinin sirləri nədir?",
            icon="/public/elements/cucumber.svg",
        ),
        cl.Starter(
            label="🌶️ İstixana",
            message="İstixanada tərəvəz yetişdirmək necə olur?",
            icon="/public/elements/greenhouse.svg",
        ),
        cl.Starter(
            label="🥔 Kartof əkini",
            message="Kartof əkini üçün ən yaxşı vaxt nə vaxtdır?",
            icon="/public/elements/potato.svg",
        ),
    ],
    "livestock": [
        cl.Starter(
            label="🐄 Mal-qara",
            message="Mal-qaranın yemləmə rejimi necə olmalıdır?",
            icon="/public/elements/cow.svg",
        ),
        cl.Starter(
            label="🐑 Qoyun",
            message="Qoyunların sağlamlığı üçün nə etmək lazımdır?",
            icon="/public/elements/sheep.svg",
        ),
        cl.Starter(
            label="🐝 Arıçılıq",
            message="Arı ailələrinin qışlaması necə təşkil olunur?",
            icon="/public/elements/bee.svg",
        ),
        cl.Starter(
            label="🏥 Baytarlıq",
            message="Heyvanların peyvəndləmə cədvəli necədir?",
            icon="/public/elements/vet.svg",
        ),
    ],
    "advanced": [
        cl.Starter(
            label="📊 Torpaq analizi",
            message="Torpaq analizinin nəticələrini şərh et",
            icon="/public/elements/soil.svg",
        ),
        cl.Starter(
            label="🔬 Xəstəlik diaqnozu",
            message="Bu bitkidə hansı xəstəlik var?",
            icon="/public/elements/microscope.svg",
        ),
        cl.Starter(
            label="📈 ROI hesablaması",
            message="Əkin planımın rentabelliyini hesabla",
            icon="/public/elements/calculator.svg",
        ),
        cl.Starter(
            label="🗺️ Peyk məlumatları",
            message="Sahəmin NDVI peyk şəkillərini göstər",
            icon="/public/elements/satellite.svg",
        ),
    ],
}

# Alias "expert" to "advanced" for chat profile compatibility
PROFILE_STARTERS["expert"] = PROFILE_STARTERS["advanced"]

# Profile-specific system prompt additions
PROFILE_PROMPTS = {
    "general": "",  # Use default system prompt
    "cotton": """
Sən pambıqçılıq üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda pambıq becərmə (Aran bölgəsi, Muğan düzü) haqqında dərin biliyə maliksən.
Pambığın vegetasiya mərhələləri, suvarma rejimi, gübrələmə normaları və zərərvericilərə qarşı mübarizə haqqında ətraflı məlumat ver.
""",
    "wheat": """
Sən taxılçılıq üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda buğda və arpa becərmə haqqında dərin biliyə maliksən.
Payızlıq və yazlıq taxıllar, don zədəsi, alaq otlarına qarşı mübarizə və məhsuldarlığın artırılması haqqında ətraflı məlumat ver.
""",
    "orchard": """
Sən meyvəçilik üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda alma, üzüm, fındıq və digər meyvə bağlarının becərilməsi haqqında dərin biliyə maliksən.
Budama, çiçəklənmə, zərərvericilərə qarşı mübarizə və məhsul yığımı haqqında ətraflı məlumat ver.
""",
    "vegetable": """
Sən tərəvəzçilik üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda pomidor, xıyar, bibər və digər tərəvəzlərin becərilməsi haqqında dərin biliyə maliksən.
İstixana və açıq sahədə tərəvəz yetişdirilməsi, suvarma və gübrələmə haqqında ətraflı məlumat ver.
""",
    "livestock": """
Sən heyvandarlıq üzrə ixtisaslaşmış mütəxəssissən.
Azərbaycanda mal-qara, qoyun, keçi və quşçuluq haqqında dərin biliyə maliksən.
Yemləmə, sağlamlıq, peyvəndləmə və məhsuldarlıq haqqında ətraflı məlumat ver.
""",
    "advanced": """
Sən kənd təsərrüfatı üzrə yüksək ixtisaslı ekspertsən.
Cavablarını daha texniki və ətraflı ver. Torpaq analizləri, bitki fiziologiyası, iqtisadi hesablamalar və GIS məlumatları daxil et.
Lazım gəldikdə elmi terminologiya istifadə et, lakin izah da ver.
""",
}


def build_combined_system_prompt(expertise_areas: list[str]) -> str:
    """Build combined system prompt from multiple expertise areas.

    Args:
        expertise_areas: List of selected expertise area IDs

    Returns:
        Combined system prompt string
    """
    if not expertise_areas:
        return ""

    prompts = []
    for area in expertise_areas:
        if area in PROFILE_PROMPTS and PROFILE_PROMPTS[area]:
            prompts.append(PROFILE_PROMPTS[area].strip())

    if not prompts:
        return ""

    # Combine with header
    combined = """
Sən çoxsahəli kənd təsərrüfatı ekspertisən. Aşağıdakı sahələrdə ixtisaslaşmısan:

""" + "\n\n".join(prompts)

    return combined


# ============================================
# THREAD PRESENTATION HELPERS
# ============================================
def build_thread_name(
    crop_type: str | None, region: str | None, planning_month: str | None = None
) -> str:
    """Generate a human-friendly thread name for the sidebar."""
    parts = []
    if crop_type:
        parts.append(crop_type)
    if region:
        parts.append(region)
    if planning_month:
        parts.append(planning_month)
    return " • ".join(parts) if parts else "Yeni söhbət"


def build_thread_tags(
    crop_type: str | None,
    region: str | None,
    expertise_ids: list[str] | None,
    action_categories: list[str] | None = None,
    experience_level: str | None = None,
    interaction_mode: str | None = None,
    llm_model: str | None = None,
) -> list[str]:
    """Produce sidebar tags so users can filter threads."""
    tags: list[str] = []
    if crop_type:
        tags.append(crop_type)
    if region:
        tags.append(region)
    if experience_level:
        tags.append(f"experience:{experience_level}")
    if expertise_ids:
        tags.extend(expertise_ids)
    if action_categories:
        tags.extend([f"plan:{cat}" for cat in action_categories])
    if interaction_mode:
        tags.append(f"mode:{interaction_mode.lower()}")
    if llm_model:
        tags.append(f"model:{llm_model}")
    # Deduplicate while keeping order
    seen = set()
    unique = []
    for tag in tags:
        if tag not in seen:
            unique.append(tag)
            seen.add(tag)
    return unique


async def update_thread_presentation(
    name: str | None,
    tags: list[str] | None,
    metadata_updates: dict | None = None,
):
    """Persist thread name/tags/metadata so the sidebar shows rich info."""
    data_layer = get_data_layer()
    thread_id = cl.user_session.get("thread_id")

    if not data_layer or not thread_id:
        return

    metadata = (cl.user_session.get("thread_metadata") or {}).copy()
    if metadata_updates:
        metadata.update(metadata_updates)

    # Keep metadata in session and push to DB
    cl.user_session.set("thread_metadata", metadata)

    try:
        await data_layer.update_thread(
            thread_id=thread_id,
            name=name,
            metadata=metadata,
            tags=tags,
        )
        logger.debug("thread_presentation_updated", thread_id=thread_id, name=name, tags=tags)
    except Exception as e:  # noqa: BLE001
        logger.warning("thread_presentation_update_failed", thread_id=thread_id, error=str(e))


# ============================================
# UI DROPDOWN → BACKEND ENDPOINT
# ============================================
ui_router = APIRouter()


class ModeModelPayload(BaseModel):
    thread_id: str
    interaction_mode: str
    llm_model: str


@ui_router.post("/ui/thread/preferences")
async def update_ui_preferences(payload: ModeModelPayload):
    """Update thread metadata and tags from client-side mode/model dropdowns."""

    allowed_modes = {"Ask", "Plan", "Agent"}
    if payload.interaction_mode not in allowed_modes:
        raise HTTPException(status_code=400, detail="Invalid interaction_mode")

    data_layer = get_data_layer()
    if not data_layer:
        raise HTTPException(status_code=503, detail="Data layer unavailable")

    # Fetch current thread to merge metadata/tags
    thread = await data_layer.get_thread(payload.thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    metadata = thread.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) if metadata.strip() else {}
        except Exception:
            metadata = {}

    # Merge and persist
    metadata.update(
        {
            "interaction_mode": payload.interaction_mode,
            "llm_model": payload.llm_model,
        }
    )

    tags = thread.get("tags") or []
    # Rebuild tags from known context to avoid growth
    tags = build_thread_tags(
        metadata.get("crop_type"),
        metadata.get("region"),
        metadata.get("expertise_areas"),
        metadata.get("action_categories"),
        metadata.get("experience_level"),
        interaction_mode=payload.interaction_mode,
        llm_model=payload.llm_model,
    )

    await data_layer.update_thread(
        thread_id=payload.thread_id,
        metadata=metadata,
        tags=tags,
    )

    return {
        "ok": True,
        "interaction_mode": payload.interaction_mode,
        "llm_model": payload.llm_model,
    }


# ============================================
# CHAT PROFILES (Header dropdown for LLM model selection)
# ============================================
# Chat Profiles appear in the header as a dropdown selector.
# This is the Chainlit-native way to let users choose between
# different LLM models (open source models from Ollama).
#
# LLM_MODEL_PROFILES is defined near the top of the file (before resolve_active_model)
# Add new models with: docker exec yonca-ollama ollama pull <model>
# ============================================


@cl.set_chat_profiles
async def chat_profiles(current_user: cl.User | None = None):
    """Define available LLM models as chat profiles.

    These appear as a dropdown in the Chainlit header, allowing users
    to switch between different open-source LLM models.

    The selected profile name IS the model name (e.g., 'qwen3:4b').
    Access via: cl.user_session.get("chat_profile")
    """
    profiles = []

    # Default model first
    default_model = demo_settings.ollama_model
    if default_model in LLM_MODEL_PROFILES:
        config = LLM_MODEL_PROFILES[default_model]
        profiles.append(
            cl.ChatProfile(
                name=default_model,
                markdown_description=config["description"],
                icon="/public/avatars/alem_1.svg",
                default=True,
                starters=PROFILE_STARTERS.get("general", []),
            )
        )

    # Add other available models
    for model_name, config in LLM_MODEL_PROFILES.items():
        if model_name != default_model:
            profiles.append(
                cl.ChatProfile(
                    name=model_name,
                    markdown_description=config["description"],
                    icon="/public/avatars/alem_1.svg",
                    starters=PROFILE_STARTERS.get("general", []),
                )
            )

    return profiles


# ============================================
# STARTERS (Context-aware conversation prompts)
# ============================================
# Starters adapt based on expertise areas selected in Chat Settings.
# Chat Profiles are now used for LLM model selection, not crop specialization.


@cl.set_starters
async def set_starters(current_user: cl.User | None = None, chat_profile: str | None = None):
    """Return starters based on expertise areas from settings.

    Since Chat Profiles are now used for LLM model selection,
    starters are determined by expertise areas in settings only.

    Args:
        current_user: The authenticated user (from OAuth)
        chat_profile: The selected LLM model name (not used for starters)
    """
    # Get expertise areas from user session settings
    try:
        settings = cl.user_session.get("chat_settings", {})
    except Exception:
        settings = {}

    expertise_areas = settings.get("expertise_areas", [])

    if expertise_areas:
        starters = []
        seen_labels = set()

        for area in expertise_areas:
            if area in PROFILE_STARTERS:
                for starter in PROFILE_STARTERS[area]:
                    if starter.label not in seen_labels:
                        starters.append(starter)
                        seen_labels.add(starter.label)

        return starters[:6] if starters else PROFILE_STARTERS["general"]

    # Default to general agriculture starters
    return PROFILE_STARTERS["general"]


# ============================================
# AUTHENTICATION (Optional Google OAuth)
# ============================================
# This allows real users (developers) to be tracked in Langfuse
# while still using synthetic farmer profiles for testing.
#
# To enable:
# 1. Create OAuth app at https://console.developers.google.com/apis/credentials
# 2. Set redirect URI: http://localhost:8501/auth/oauth/google/callback
# 3. Set environment variables:
#    - OAUTH_GOOGLE_CLIENT_ID
#    - OAUTH_GOOGLE_CLIENT_SECRET
#    - CHAINLIT_AUTH_SECRET (any random string)
#
# AVAILABLE USER DATA (by scope):
# ─────────────────────────────────────────────────────────────────────────
# Standard (no extra consent):
#   - email, name, picture, given_name, family_name, locale, google_id
#   - hosted_domain (hd) - for Google Workspace users
#
# Sensitive (requires Google app verification + user consent):
#   - birthday: scope=user.birthday.read
#   - gender: scope=user.gender.read
#   - phone: scope=user.phonenumbers.read
#   - address: scope=user.addresses.read
#   - age_range: scope=profile.agerange.read
# ─────────────────────────────────────────────────────────────────────────


def is_oauth_enabled() -> bool:
    """Check if OAuth is configured."""
    return bool(os.getenv("OAUTH_GOOGLE_CLIENT_ID") and os.getenv("OAUTH_GOOGLE_CLIENT_SECRET"))


async def fetch_google_people_api(access_token: str) -> dict:
    """Fetch enhanced user profile from Google People API.

    This requires additional OAuth scopes configured in Google Cloud Console:
    - https://www.googleapis.com/auth/user.birthday.read
    - https://www.googleapis.com/auth/user.gender.read
    - https://www.googleapis.com/auth/user.phonenumbers.read
    - https://www.googleapis.com/auth/user.addresses.read

    Note: These are "sensitive scopes" and require Google app verification
    before they can be used in production.

    Args:
        access_token: OAuth access token from Google login

    Returns:
        Dict with enhanced profile fields (birthday, gender, phone, address)
    """
    import httpx

    # Request specific person fields from People API
    person_fields = "birthdays,genders,phoneNumbers,addresses,locales,ageRanges"
    url = f"https://people.googleapis.com/v1/people/me?personFields={person_fields}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers={"Authorization": f"Bearer {access_token}"}, timeout=10.0
            )

            if response.status_code != 200:
                logger.warning(
                    "people_api_error", status=response.status_code, detail=response.text[:200]
                )
                return {}

            data = response.json()

            # Extract fields from People API response
            result = {}

            # Birthday (may have year/month/day or just month/day for privacy)
            if birthdays := data.get("birthdays"):
                for bday in birthdays:
                    if date := bday.get("date"):
                        result["birthday"] = {
                            "year": date.get("year"),
                            "month": date.get("month"),
                            "day": date.get("day"),
                        }
                        break

            # Gender
            if genders := data.get("genders"):
                for gender in genders:
                    if value := gender.get("value"):
                        result["gender"] = value
                        break

            # Phone number (primary)
            if phones := data.get("phoneNumbers"):
                for phone in phones:
                    if value := phone.get("value"):
                        result["phone"] = value
                        result["phone_type"] = phone.get("type", "unknown")
                        break

            # Address (primary)
            if addresses := data.get("addresses"):
                for addr in addresses:
                    result["address"] = {
                        "formatted": addr.get("formattedValue"),
                        "city": addr.get("city"),
                        "region": addr.get("region"),
                        "country": addr.get("country"),
                        "country_code": addr.get("countryCode"),
                        "postal_code": addr.get("postalCode"),
                    }
                    break

            # Age range (less sensitive than exact birthday)
            if age_ranges := data.get("ageRanges"):
                for ar in age_ranges:
                    if value := ar.get("ageRange"):
                        result["age_range"] = value  # e.g., "TWENTY_ONE_OR_OLDER"
                        break

            logger.info("people_api_success", fields_retrieved=list(result.keys()))

            return result

    except Exception as e:
        logger.error("people_api_exception", error=str(e))
        return {}


# Only register OAuth callback if credentials are configured
# This prevents Chainlit from requiring OAuth env vars at startup
if is_oauth_enabled():

    @cl.oauth_callback
    async def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: dict[str, str],
        default_user: cl.User,
        _id_token: str | None = None,
    ) -> cl.User | None:
        """Handle OAuth callback from Google with enhanced user profile data.

        This captures all available user info from Google OAuth:
        - Basic: email, name, picture (always available)
        - Profile: given_name, family_name, locale (with 'profile' scope)
        - Domain: hd (Google Workspace hosted domain, if applicable)

        For additional data (birthday, gender, phone, address), you would need:
        1. Add scopes to Google OAuth config (requires Google app verification)
        2. Call People API with the access token

        Args:
            provider_id: OAuth provider (e.g., "google")
            token: OAuth access token (can be used for additional API calls)
            raw_user_data: User info from provider's userinfo endpoint
            default_user: Chainlit's default user object
            _id_token: Optional ID token

        Returns:
            cl.User if allowed, None to deny access.
        """
        if provider_id == "google":
            # ═══════════════════════════════════════════════════════════════
            # STANDARD PROFILE DATA (available with openid + profile + email)
            # ═══════════════════════════════════════════════════════════════
            email = raw_user_data.get("email", "unknown")
            name = raw_user_data.get("name", email)
            picture = raw_user_data.get("picture")

            # Additional fields available by default from Google OAuth
            given_name = raw_user_data.get("given_name")  # First name
            family_name = raw_user_data.get("family_name")  # Last name
            locale = raw_user_data.get("locale")  # Language/region (e.g., "en", "az")
            email_verified = raw_user_data.get("email_verified", False)

            # Google Workspace domain (only for workspace/organization accounts)
            hosted_domain = raw_user_data.get("hd")  # e.g., "yonca.az"

            # Google user ID (unique, stable identifier)
            google_id = raw_user_data.get("sub")

            logger.info(
                "oauth_login_standard",
                provider=provider_id,
                email=email,
                name=name,
                given_name=given_name,
                family_name=family_name,
                locale=locale,
                hosted_domain=hosted_domain,
                email_verified=email_verified,
            )

            # ═══════════════════════════════════════════════════════════════
            # NOTE: People API (birthday, gender, phone, address) NOT used
            # ═══════════════════════════════════════════════════════════════
            # People API sensitive scopes require Google app verification
            # which costs $15k-75k and is not practical for this demo.
            # We use only FREE data from standard OAuth scopes.
            #
            # See: https://support.google.com/cloud/answer/9110914

            # Return user with FREE metadata only (no paid APIs)
            return cl.User(
                identifier=email,
                metadata={
                    # ════════════════════════════════════════════════════════
                    # ALL FIELDS BELOW ARE 100% FREE (standard OAuth scopes)
                    # ════════════════════════════════════════════════════════
                    # Core identity (openid scope)
                    "name": name,
                    "email": email,
                    "email_verified": email_verified,
                    "image": picture,  # Chainlit expects 'image' for avatar
                    "picture": picture,  # Keep 'picture' too for compatibility
                    "provider": provider_id,
                    "google_id": google_id,
                    # Profile details (profile scope - FREE)
                    "given_name": given_name,
                    "family_name": family_name,
                    "locale": locale,  # Language/region: "az", "en", "ru"
                    # Organization (FREE - only for Google Workspace accounts)
                    "hosted_domain": hosted_domain,  # e.g., "zekalab.com"
                },
            )

        # Allow other providers with default user
        return default_user


# ============================================
# LOCALIZATION
# ============================================
AZ_STRINGS = {
    "welcome": "**ALEM | Aqronom Assistentiniz**\n\nSalam! Mən ALEM-əm, sizin virtual aqronomun. Əkin, suvarma, gübrələmə və digər kənd təsərrüfatı məsələlərində kömək edə bilərəm.",
    "farm_loaded": "📍 Təsərrüfat məlumatları yükləndi",
    "thinking": "Düşünürəm...",
    "error": "❌ Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.",
    "select_farm": "Təsərrüfat seçin",
    # Dashboard strings
    "farm_status": "Təsərrüfat vəziyyəti",
    "status_normal": "Normal",
    "status_attention": "Diqqət tələb edir",
    # Action buttons - emoji removed (Chainlit renders visual indicators)
    "weather": "Hava",
    "subsidy": "Subsidiya",
    "irrigation": "Suvarma",
    "sima_auth": "SİMA inteqrasiyası hazır",
    "quick_actions": "Sürətli əməliyyatlar",
    # Settings strings
    "settings_language": "Dil / Language",
    "settings_notifications": "Bildirişlər",
    "settings_detail_level": "Cavab təfərrüatı",
    "settings_units": "Ölçü vahidləri",
    "settings_currency": "Valyuta",
}


# ============================================
# CHAT SETTINGS (User Preferences Sidebar)
# ============================================
# This is the native Chainlit way to handle per-user settings.
# Settings appear in the sidebar and persist per session.
# With data layer enabled, settings are ALSO persisted to database
# and restored when the user logs in again.
# ============================================
async def setup_chat_settings(user: cl.User | None = None):
    """Initialize chat settings panel for user preferences.

    These settings appear in Chainlit's sidebar when the user clicks
    the settings icon. Values are stored in cl.user_session["chat_settings"].

    If data persistence is enabled and user is authenticated,
    settings are loaded from database (persisted across sessions).

    SMART DEFAULTS:
    - Expertise areas are auto-detected from ALEM persona (crop type + experience)
    - User can override by selecting different areas
    - Selections persist across sessions

    Args:
        user: Authenticated user (from OAuth) for loading persisted settings
    """
    # Load persisted settings if user is authenticated
    persisted = await load_user_settings(user)

    # ─────────────────────────────────────────────────────────────
    # SMART DEFAULTS: Detect expertise from ALEM persona
    # ─────────────────────────────────────────────────────────────
    alem_persona = cl.user_session.get("alem_persona")
    default_expertise = detect_expertise_from_persona(alem_persona)

    # Use persisted expertise if available, otherwise use smart defaults
    expertise_areas = persisted.get("expertise_areas", default_expertise)

    # Log what we're using
    logger.info(
        "chat_settings_expertise",
        default_expertise=default_expertise,
        persisted_expertise=persisted.get("expertise_areas"),
        using_expertise=expertise_areas,
        persona_crop=alem_persona.get("crop_type") if alem_persona else None,
    )

    # Map persisted values to initial indices
    language_values = ["Azərbaycanca", "English", "Русский"]
    detail_values = ["Qısa", "Orta", "Ətraflı"]
    unit_values = ["Metrik (ha, kg)", "Yerli (sotka, pud)"]
    currency_values = ["₼ AZN (Manat)", "$ USD (Dollar)", "€ EUR (Euro)"]
    mode_values = ["Ask", "Plan", "Agent"]
    model_values = [
        demo_settings.ollama_model,
        "llama3.1",
        "qwen2.5",
        "mixtral-8x7b",
    ]

    # Expertise area values with Azerbaijani labels
    expertise_values = [
        ("general", "🌾 Ümumi kənd təsərrüfatı"),
        ("cotton", "🧵 Pambıqçılıq"),
        ("wheat", "🌾 Taxılçılıq (buğda, arpa)"),
        ("orchard", "🍎 Meyvəçilik (alma, üzüm)"),
        ("vegetable", "🥬 Tərəvəzçilik"),
        ("livestock", "🐄 Heyvandarlıq"),
        ("advanced", "🔬 Qabaqcıl texnologiyalar"),
    ]

    language_idx = (
        language_values.index(persisted.get("language", "Azərbaycanca"))
        if persisted.get("language") in language_values
        else 0
    )
    detail_idx = (
        detail_values.index(persisted.get("detail_level", "Orta"))
        if persisted.get("detail_level") in detail_values
        else 1
    )
    units_idx = (
        unit_values.index(persisted.get("units", "Metrik (ha, kg)"))
        if persisted.get("units") in unit_values
        else 0
    )
    currency_idx = (
        currency_values.index(persisted.get("currency", "₼ AZN (Manat)"))
        if persisted.get("currency") in currency_values
        else 0
    )

    mode_idx = (
        mode_values.index(persisted.get("interaction_mode", "Ask"))
        if persisted.get("interaction_mode") in mode_values
        else 0
    )

    model_idx = (
        model_values.index(persisted.get("llm_model", demo_settings.ollama_model))
        if persisted.get("llm_model") in model_values
        else 0
    )

    settings = await cl.ChatSettings(
        [
            # ═══════════════════════════════════════════════════════════════
            # FARM PROFILE (Yonca Mobile App Fields)
            # ═══════════════════════════════════════════════════════════════
            Select(
                id="crop_type",
                label="Əsas məhsul / Primary Crop",
                values=[
                    # Danli (Grains) - 🌾
                    "Buğda (Wheat) [Dənli]",
                    "Arpa (Barley) [Dənli]",
                    "Çəltik (Rice) [Dənli]",
                    "Vələmir (Oats) [Dənli]",
                    "Çovdar (Rye) [Dənli]",
                    # Taravaz (Vegetables) - 🥬
                    "Pomidor (Tomato) [Tərəvəz]",
                    "Xıyar (Cucumber) [Tərəvəz]",
                    "Kartof (Potato) [Tərəvəz]",
                    "Kələm (Cabbage) [Tərəvəz]",
                    "Badımcan (Eggplant) [Tərəvəz]",
                    "Bibər (Pepper) [Tərəvəz]",
                    "Soğan (Onion) [Tərəvəz]",
                    "Sarımsaq (Garlic) [Tərəvəz]",
                    # Texniki (Technical) - 🏭
                    "Pambıq (Cotton) [Texniki]",
                    "Tütün (Tobacco) [Texniki]",
                    "Şəkər çuğunduru (Sugar Beet) [Texniki]",
                    "Günəbaxan (Sunflower) [Texniki]",
                    "Qarğıdalı (Corn) [Texniki]",
                    "Çay (Tea) [Texniki]",
                    # Yem (Feed) - 🌿
                    "Yonca (Alfalfa) [Yem]",
                    "Gülül (Vetch) [Yem]",
                    # Meyva (Fruits) - 🍎
                    "Üzüm (Grape) [Meyvə]",
                    "Nar (Pomegranate) [Meyvə]",
                    "Gilas (Cherry) [Meyvə]",
                    "Alma (Apple) [Meyvə]",
                    "Armud (Pear) [Meyvə]",
                    "Heyva (Quince) [Meyvə]",
                    "Qoz (Walnut) [Meyvə]",
                    "Fındıq (Hazelnut) [Meyvə]",
                    "Zeytun (Olive) [Meyvə]",
                    "Sitrus (Citrus) [Meyvə]",
                    # Bostan (Melons) - 🍉
                    "Qarpız (Watermelon) [Bostan]",
                    "Yemiş (Melon) [Bostan]",
                    "Boranı (Pumpkin) [Bostan]",
                ],
                initial_index=0
                if not alem_persona
                else [
                    "Pambıq (Cotton)",
                    "Buğda (Wheat)",
                    "Arpa (Barley)",
                    "Qarğıdalı (Corn)",
                    "Alma (Apple)",
                    "Üzüm (Grape)",
                ].index(alem_persona.get("crop_type", "Pambıq (Cotton)"))
                if alem_persona.get("crop_type")
                in ["Pambıq", "Buğda", "Arpa", "Qarğıdalı", "Alma", "Üzüm"]
                else 0,
                description="Təsərrüfatınızda əkin etdiyiniz əsas məhsul",
            ),
            Select(
                id="region",
                label="Region",
                values=[
                    "Aran",
                    "Quba-Xaçmaz",
                    "Şəki-Zaqatala",
                    "Mil-Muğan",
                    "Lənkəran-Astara",
                    "Gəncə-Qazax",
                    "Naxçıvan",
                    "Qarabağ",
                ],
                initial_index=0 if not alem_persona else 0,
                description="Təsərrüfatınızın yerləşdiyi iqtisadi region",
            ),
            NumberInput(
                id="farm_size_ha",
                label="Sahə (hektar) / Farm Size (ha)",
                initial=alem_persona.get("farm_size_ha", 5.0) if alem_persona else 5.0,
                min=0.5,
                max=500.0,
                step=0.5,
                description="Təsərrüfatınızın ümumi sahəsi",
            ),
            Select(
                id="experience_level",
                label="Təcrübə səviyyəsi / Experience Level",
                values=[
                    "Başlanğıc / Novice",
                    "Orta / Intermediate",
                    "Mütəxəssis / Expert",
                ],
                initial_index=1
                if not alem_persona
                else (
                    ["novice", "intermediate", "expert"].index(
                        alem_persona.get("experience_level", "intermediate")
                    )
                ),
                description="Kənd təsərrüfatı təcrübəniz",
            ),
            Select(
                id="soil_type",
                label="Torpaq növü / Soil Type",
                values=[
                    "Gilli / Clay",
                    "Qumlu / Sandy",
                    "Lopam / Loam",
                    "Şoranlı / Saline",
                ],
                initial_index=2,
                description="Təsərrüfatınızın əsas torpaq növü",
            ),
            Select(
                id="irrigation_type",
                label="Suvarma sistemi / Irrigation System",
                values=[
                    "Damcı / Drip",
                    "Pivot",
                    "Şırım / Flood",
                    "Yağış / Rainfed",
                ],
                initial_index=0,
                description="İstifadə etdiyiniz suvarma üsulu",
            ),
            # ═══════════════════════════════════════════════════════════════
            # PLANNING & ACTIONS (Yonca Planner Features)
            # ═══════════════════════════════════════════════════════════════
            Select(
                id="planning_month",
                label="Planlaşdırma ayı / Planning Month",
                values=[
                    "Yanvar / January",
                    "Fevral / February",
                    "Mart / March",
                    "Aprel / April",
                    "May / May",
                    "İyun / June",
                    "İyul / July",
                    "Avqust / August",
                    "Sentyabr / September",
                    "Oktyabr / October",
                    "Noyabr / November",
                    "Dekabr / December",
                ],
                initial_index=0,  # Current month (January)
                description="Hansı ay üçün planlaşdırma görmək istəyirsiniz?",
            ),
            MultiSelect(
                id="action_categories",
                label="Fəaliyyət kateqoriyaları / Action Categories",
                values=[
                    "Əkin / Planting",
                    "Suvarma / Irrigation",
                    "Gübrələmə / Fertilization",
                    "Zərərverici mübarizə / Pest Control",
                    "Məhsul yığımı / Harvest",
                    "Torpaq işləri / Soil Work",
                    "Budama / Pruning",
                    "İqlim monitorinqi / Weather Monitoring",
                ],
                initial_value=[
                    "Əkin / Planting",
                    "Suvarma / Irrigation",
                    "Gübrələmə / Fertilization",
                ],
                description="Hansı fəaliyyətlər üzrə məsləhət almaq istəyirsiniz?",
            ),
            # ═══════════════════════════════════════════════════════════════
            # EXPERTISE AREAS — Multi-select with smart defaults
            # ═══════════════════════════════════════════════════════════════
            MultiSelect(
                id="expertise_areas",
                label="Ekspertiza sahələri / Expertise Areas",
                values=[label for _, label in expertise_values],
                initial_value=[
                    label for area_id, label in expertise_values if area_id in expertise_areas
                ],
                description="Hansı sahələrdə məsləhət almaq istəyirsiniz? (Birdən çox seçə bilərsiniz)",
            ),
            # ═══════════════════════════════════════════════════════════════
            # UI PREFERENCES
            # ═══════════════════════════════════════════════════════════════
            Select(
                id="language",
                label=AZ_STRINGS["settings_language"],
                values=language_values,
                initial_index=language_idx,
                description="Yonca cavablarının dili",
            ),
            Select(
                id="currency",
                label=AZ_STRINGS["settings_currency"],
                values=currency_values,
                initial_index=currency_idx,
                description="Qiymətlər və subsidiyalar üçün valyuta",
            ),
            Select(
                id="detail_level",
                label=AZ_STRINGS["settings_detail_level"],
                values=detail_values,
                initial_index=detail_idx,
                description="Cavabların nə qədər ətraflı olacağı",
            ),
            Select(
                id="units",
                label=AZ_STRINGS["settings_units"],
                values=unit_values,
                initial_index=units_idx,
                description="Sahə və çəki ölçü vahidləri",
            ),
            Switch(
                id="notifications",
                label=AZ_STRINGS["settings_notifications"],
                initial=persisted.get("notifications", True),
                description="Suvarma və hava xəbərdarlıqları",
            ),
            Switch(
                id="show_sources",
                label="Mənbələri göstər",
                initial=persisted.get("show_sources", False),
                description="Tövsiyələrin mənbəyini göstər",
            ),
            Switch(
                id="show_thinking_steps",
                label="🧠 Düşüncə prosesini göstər / Show Thinking Steps",
                initial=persisted.get("show_thinking_steps", demo_settings.enable_thinking_steps),
                description="ALEM-in hər addımını göstər (kontekst yükləmə, təhlil, cavab hazırlama)",
            ),
            Select(
                id="interaction_mode",
                label="Rejim / Mode",
                values=mode_values,
                initial_index=mode_idx,
                description="Ask (sürətli cavab), Plan (addım-addım), Agent (ətraflı əməliyyat)",
            ),
            Select(
                id="llm_model",
                label="Model",
                values=model_values,
                initial_index=model_idx,
                description="İstifadə ediləcək model (placeholder seçim — hazırkı sessiyada eyni model istifadə olunur)",
            ),
        ]
    ).send()

    # Store expertise areas in session for starters and prompts
    cl.user_session.set(
        "chat_settings",
        {
            **persisted,
            "expertise_areas": expertise_areas,
        },
    )

    return settings


# Map expertise labels back to IDs (for processing settings)
EXPERTISE_LABEL_TO_ID = {
    "🌾 Ümumi kənd təsərrüfatı": "general",
    "🧵 Pambıqçılıq": "cotton",
    "🌾 Taxılçılıq (buğda, arpa)": "wheat",
    "🍎 Meyvəçilik (alma, üzüm)": "orchard",
    "🥬 Tərəvəzçilik": "vegetable",
    "🐄 Heyvandarlıq": "livestock",
    "🔬 Qabaqcıl texnologiyalar": "advanced",
}


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle user settings changes.

    Called when user modifies any setting in the sidebar.
    Settings are automatically stored in cl.user_session["chat_settings"].

    If data persistence is enabled, settings are ALSO saved to database
    so they persist across sessions.

    Special handling for:
    - expertise_areas: Converts labels back to IDs for internal use
    - Farm profile fields: Updates agent context with crop/region/size
    - Planning fields: Triggers month-by-month action generation
    """
    user: cl.User | None = cl.user_session.get("user")

    # ═══════════════════════════════════════════════════════════════
    # FARM PROFILE FIELDS — Extract and normalize
    # ═══════════════════════════════════════════════════════════════
    crop_type_raw = settings.get("crop_type", "Pambıq (Cotton) [Texniki]")
    # Extract crop name: "Pambıq (Cotton) [Texniki]" → "Pambıq"
    crop_type = (
        crop_type_raw.split("(")[0].strip()
        if "(" in crop_type_raw
        else crop_type_raw.split("[")[0].strip()
    )

    region = settings.get("region", "Aran")
    farm_size_ha = settings.get("farm_size_ha", 5.0)

    experience_raw = settings.get("experience_level", "Orta / Intermediate")
    experience = experience_raw.split("/")[0].strip().lower()  # "Orta / Intermediate" → "orta"
    # Map Azerbaijani experience to English keys
    experience_map = {"başlanğıc": "novice", "orta": "intermediate", "mütəxəssis": "expert"}
    experience_level = experience_map.get(experience, "intermediate")

    soil_type_raw = settings.get("soil_type", "Lopam / Loam")
    soil_type = soil_type_raw.split("/")[0].strip()

    irrigation_raw = settings.get("irrigation_type", "Damcı / Drip")
    irrigation_type = irrigation_raw.split("/")[0].strip()

    # ═══════════════════════════════════════════════════════════════
    # PLANNING FIELDS — Extract month and action categories
    # ═══════════════════════════════════════════════════════════════
    planning_month_raw = settings.get("planning_month", "Yanvar / January")
    planning_month = planning_month_raw.split("/")[1].strip()  # "Yanvar / January" → "January"

    action_categories_raw = settings.get("action_categories", [])
    action_categories = [cat.split("/")[0].strip() for cat in action_categories_raw]

    # ═══════════════════════════════════════════════════════════════
    # EXPERTISE AREAS — Convert labels to IDs
    # ═══════════════════════════════════════════════════════════════
    raw_expertise = settings.get("expertise_areas", [])

    # Convert labels to IDs
    expertise_ids = []
    for label in raw_expertise:
        if label in EXPERTISE_LABEL_TO_ID:
            expertise_ids.append(EXPERTISE_LABEL_TO_ID[label])
        elif label in EXPERTISE_AREAS:  # Already an ID
            expertise_ids.append(label)

    # Store normalized settings with IDs and parsed fields
    normalized_settings = {
        **settings,
        "expertise_areas": expertise_ids,
        "crop_type_clean": crop_type,
        "experience_level_clean": experience_level,
        "soil_type_clean": soil_type,
        "irrigation_type_clean": irrigation_type,
        "planning_month_clean": planning_month,
        "action_categories_clean": action_categories,
        "interaction_mode": settings.get("interaction_mode", "Ask"),
        "llm_model": settings.get("llm_model", demo_settings.ollama_model),
    }

    logger.info(
        "settings_updated",
        session_id=cl.user_session.get("id"),
        user=user.identifier if user else "anonymous",
        farm_profile={
            "crop": crop_type,
            "region": region,
            "size_ha": farm_size_ha,
            "experience": experience_level,
            "soil": soil_type,
            "irrigation": irrigation_type,
        },
        planning={
            "month": planning_month,
            "categories": action_categories,
        },
        expertise_ids=expertise_ids,
        interaction_mode=normalized_settings["interaction_mode"],
        llm_model=normalized_settings["llm_model"],
    )

    # Update session with normalized settings
    cl.user_session.set("chat_settings", normalized_settings)

    # ═══════════════════════════════════════════════════════════════
    # BUILD AGROTECHNOLOGICAL CALENDAR PROMPT
    # ═══════════════════════════════════════════════════════════════
    # Import agro calendar prompt builder
    import sys
    from pathlib import Path

    prompts_path = Path(__file__).parent.parent / "prompts"
    if str(prompts_path) not in sys.path:
        sys.path.insert(0, str(prompts_path))

    try:
        from agro_calendar_prompts import build_agro_calendar_prompt

        # Map crop to category (matches YONCA Agrotechnological Calendar standard)
        crop_to_category = {
            # Danli (Grains)
            "Buğda": "Danli",
            "Arpa": "Danli",
            "Çəltik": "Danli",
            "Vələmir": "Danli",
            "Çovdar": "Danli",
            # Taravaz (Vegetables)
            "Pomidor": "Taravaz",
            "Xıyar": "Taravaz",
            "Kartof": "Taravaz",
            "Kələm": "Taravaz",
            "Badımcan": "Taravaz",
            "Bibər": "Taravaz",
            "Soğan": "Taravaz",
            "Sarımsaq": "Taravaz",
            # Texniki (Technical/Industrial)
            "Pambıq": "Texniki",
            "Tütün": "Texniki",
            "Şəkər çuğunduru": "Texniki",
            "Günəbaxan": "Texniki",
            "Qarğıdalı": "Texniki",
            "Çay": "Texniki",
            # Yem (Feed/Fodder)
            "Yonca": "Yem",
            "Gülül": "Yem",
            # Meyva (Fruits)
            "Üzüm": "Meyva",
            "Nar": "Meyva",
            "Gilas": "Meyva",
            "Alma": "Meyva",
            "Armud": "Meyva",
            "Heyva": "Meyva",
            "Qoz": "Meyva",
            "Fındıq": "Meyva",
            "Zeytun": "Meyva",
            "Sitrus": "Meyva",
            # Bostan (Melons/Gourds)
            "Qarpız": "Bostan",
            "Yemiş": "Bostan",
            "Boranı": "Bostan",
        }

        crop_category = crop_to_category.get(crop_type, "Danli")

        # Build scenario for prompt generation
        scenario = {
            "crop_category": crop_category,
            "specific_crop": crop_type,
            "region": region,
            "current_month": planning_month,
            "farm_size_ha": farm_size_ha,
            "experience_level": experience_level,
            "soil_type": soil_type,
            "irrigation_type": irrigation_type,
            "action_categories": action_categories,
            "conversation_stage": cl.user_session.get("conversation_stage", "profile_setup"),
        }

        # Generate agrotechnological calendar prompt
        agro_prompt = build_agro_calendar_prompt(scenario)

        # Combine with expertise-based prompts
        combined_prompt = build_combined_system_prompt(expertise_ids)
        combined_prompt += f"\n\n{agro_prompt}"

        # Store scenario context in session for LangGraph state
        cl.user_session.set("scenario_context", scenario)
        cl.user_session.set("profile_prompt", combined_prompt)

        logger.info(
            "scenario_context_updated",
            crop_category=crop_category,
            specific_crop=crop_type,
            region=region,
            month=planning_month,
            conversation_stage=scenario["conversation_stage"],
            settings_version=cl.user_session.get("settings_version", 1),
        )

        # Increment settings version to track evolution
        current_version = cl.user_session.get("settings_version", 0)
        cl.user_session.set("settings_version", current_version + 1)

        # Persist scenario to database for session resumption
        user_id = cl.user_session.get("user_id", "anonymous")
        thread_id = cl.user_session.get("thread_id")
        if thread_id:
            await save_farm_scenario(
                user_id=user_id,
                thread_id=thread_id,
                scenario=scenario,
            )

        logger.info(
            "scenario_context_updated",
            crop_category=crop_category,
            specific_crop=crop_type,
            region=region,
            month=planning_month,
            conversation_stage=scenario["conversation_stage"],
            settings_version=cl.user_session.get("settings_version", 1),
        )

        # Increment settings version to track evolution
        current_version = cl.user_session.get("settings_version", 0)
        cl.user_session.set("settings_version", current_version + 1)

    except ImportError:
        logger.warning("agro_calendar_prompts not found, using basic farm context")
        # Fallback to basic farm context
        combined_prompt = build_combined_system_prompt(expertise_ids)
        farm_context = f"""

FARM PROFILE:
- Primary Crop: {crop_type}
- Region: {region}
- Farm Size: {farm_size_ha} ha
- Experience: {experience_level}
- Soil Type: {soil_type}
- Irrigation: {irrigation_type}

When providing recommendations, consider these farm-specific details.
"""
        combined_prompt += farm_context
        cl.user_session.set("profile_prompt", combined_prompt)

    # Persist settings to database if user is authenticated
    if user:
        saved = await save_user_settings(user, normalized_settings)
        if saved:
            logger.info("settings_persisted", user=user.identifier)

    # Update thread presentation so sidebar shows farm context
    thread_name = build_thread_name(
        crop_type=crop_type, region=region, planning_month=planning_month
    )
    thread_tags = build_thread_tags(
        crop_type=crop_type,
        region=region,
        expertise_ids=expertise_ids,
        action_categories=action_categories,
        experience_level=experience_level,
        interaction_mode=normalized_settings["interaction_mode"],
        llm_model=normalized_settings["llm_model"],
    )
    await update_thread_presentation(
        name=thread_name,
        tags=thread_tags,
        metadata_updates={
            "crop_type": crop_type,
            "region": region,
            "farm_size_ha": farm_size_ha,
            "experience_level": experience_level,
            "planning_month": planning_month,
            "action_categories": action_categories,
            "interaction_mode": normalized_settings["interaction_mode"],
            "llm_model": normalized_settings["llm_model"],
        },
    )

    # TODO: Save scenario to farm_scenario_plans table
    # This enables scenario retrieval on chat resume and tracking evolution
    # await save_farm_scenario(user_id=user.identifier if user else None,
    #                          thread_id=cl.user_session.get("thread_id"),
    #                          scenario=scenario)

    # ═══════════════════════════════════════════════════════════════
    # PLANNING TRIGGER — Generate month-by-month actions if requested
    # ═══════════════════════════════════════════════════════════════
    if action_categories:
        # This will be integrated with rules engine to generate monthly plans
        # For now, log the request
        logger.info(
            "planning_requested",
            month=planning_month,
            categories=action_categories,
            crop=crop_type,
            region=region,
        )

    # Acknowledge the change to user with comprehensive summary
    language = settings.get("language", "Azərbaycanca")

    # Build summary message
    if expertise_ids:
        expertise_names = [EXPERTISE_AREAS.get(e, e) for e in expertise_ids]
        expertise_summary = ", ".join(expertise_names)
    else:
        expertise_summary = "Ümumi"

    farm_summary = f"{crop_type} • {region} • {farm_size_ha} ha"

    if language == "English":
        msg = f"Settings updated\n\n**Farm Profile:** {farm_summary}\n**Expertise:** {expertise_summary}"
        if action_categories:
            msg += f"\n**Planning:** {planning_month} - {len(action_categories)} categories"
        await cl.Message(content=msg).send()
    elif language == "Русский":
        msg = f"Настройки обновлены\n\n**Профиль фермы:** {farm_summary}\n**Области экспертизы:** {expertise_summary}"
        if action_categories:
            msg += f"\n**Планирование:** {planning_month} - {len(action_categories)} категорий"
        await cl.Message(content=msg).send()
    else:
        msg = f"Parametrlər yeniləndi\n\n**Təsərrüfat profili:** {farm_summary}\n**Ekspertiza sahələri:** {expertise_summary}"
        if action_categories:
            msg += f"\n**Planlaşdırma:** {planning_month} - {len(action_categories)} kateqoriya"
        await cl.Message(content=msg).send()


# ============================================
# DASHBOARD WELCOME (Agricultural Command Center)
# ============================================
# WELCOME EXPERIENCE ARCHITECTURE:
# After OAuth login, users see TWO welcome elements:
#
# 1. MAIN CHAT (this function): send_dashboard_welcome()
#    - Primary greeting (personalized with user's first name)
#    - Farm status display (normal/attention indicators)
#    - Quick action buttons (Weather, Subsidy, Irrigation)
#    - Focus: Immediate interaction, farm context, action-oriented
#
# 2. SIDEBAR: render_dashboard_sidebar() (from insights_dashboard.py)
#    - Usage analytics (conversations, tokens, streak)
#    - Activity heatmap (last 90 days)
#    - Link to Langfuse for drill-down
#    - Focus: Secondary context, non-intrusive, analytics
#
# Why Two Messages?
# - Main chat: Conversation-focused (users talk to ALEM here)
# - Sidebar: Data-focused (users check stats here)
# - Separation respects Chainlit's UI philosophy (chat ≠ sidebar)
#
# Render Sequence (in @on_chat_start):
#   1. Load Langfuse stats
#   2. Render sidebar dashboard (non-blocking background context)
#   3. Send main welcome message (primary user attention)
#
# BRANDING NOTE: Use "ALEM" as primary agent name. "Yonca" is the internal project name.
# AVOID: "Sidecar" (internal term), "DigiRella", "ZekaLab" (business names)
# ============================================
async def send_dashboard_welcome(user: cl.User | None = None):
    """Send primary welcome message to main chat with farm status and quick actions.

    This is the FIRST message users see after logging in (main chat).
    Displays personalized greeting, farm context, and action buttons.

    Companion to: render_dashboard_sidebar() (analytics in sidebar)

    Creates a "Warm Handshake" experience that transforms the chat from
    a generic interface into an agricultural command center.

    Args:
        user: Optional authenticated user for personalization
    """
    try:
        # Personalized greeting
        if user and user.metadata:
            user_name = user.metadata.get("name", "").split()[0]  # First name
            greeting = f"Salam, **{user_name}**! 👋"
        else:
            greeting = "Xoş gəlmisiniz! 👋"

        # Build dashboard message using native markdown (more compatible than inline HTML)
        dashboard_content = f"""{greeting}

🌿 **ALEM | Aqronom Assistentiniz**

Mən sizin virtual aqronomam — əkin, suvarma və subsidiya məsələlərində kömək edirəm.

**📊 Sistem Vəziyyəti:**
- ✓ Normal
- ✓ SİMA inteqrasiyası hazır

---

**Sürətli Əməliyyatlar** — Aşağıdakı düymələrə klikləyin:
"""

        # Create quick action buttons using Chainlit Actions (NO duplicated emojis)
        actions = [
            cl.Action(
                name="weather",
                payload={"action": "weather"},
                label="🌤️ " + AZ_STRINGS["weather"],
            ),
            cl.Action(
                name="subsidy",
                payload={"action": "subsidy"},
                label="📋 " + AZ_STRINGS["subsidy"],
            ),
            cl.Action(
                name="irrigation",
                payload={"action": "irrigation"},
                label="💧 " + AZ_STRINGS["irrigation"],
            ),
        ]

        # Send the dashboard welcome message
        await cl.Message(
            content=dashboard_content,
            author="ALEM",
            actions=actions,
        ).send()

        logger.info("welcome_message_sent", user_id=user.identifier if user else "anonymous")

    except Exception as e:
        logger.error("welcome_message_failed", error=str(e), exc_info=True)
        # Fallback simple welcome
        await cl.Message(content="👋 Xoş gəlmisiniz! Mən ALEM-əm, sizin virtual aqronomun.").send()


# ============================================
# NATIVE CHAINLIT ARCHITECTURE NOTE
# ============================================
# ✅ QUICK ACTIONS: Use @cl.set_starters (profile-aware)
# ✅ ALSO NEED: @cl.action_callback for Action elements
#
# Why?
# - @cl.set_starters are message starters (auto-handled)
# - @cl.Action elements are buttons (need explicit callbacks)
# - Both patterns coexist in this demo
#
# When user clicks Action button → @on_action fires
# When user clicks starter → Message sent → @on_message handles it
#
# See: CHAINLIT-NATIVE-ARCHITECTURE.md for full architecture
# ============================================


# ============================================
# QUICK ACTION CALLBACKS (Weather, Subsidy, Irrigation)
# ============================================
# These handle the quick-action buttons in the dashboard
# Users click buttons → generates specialized context → calls @on_message


@cl.action_callback("confirm_action")
async def on_confirm_action(action: cl.Action):
    """Handle confirm action button clicks."""
    await cl.Message(content=f"✅ Action confirmed: {action.value}").send()
    await action.remove()


@cl.action_callback("cancel_action")
async def on_cancel_action(action: cl.Action):
    """Handle cancel action button clicks."""
    await cl.Message(content="❌ Action cancelled").send()
    await action.remove()


@cl.action_callback("feedback_positive")
async def on_feedback_positive(action: cl.Action):
    """Handle positive feedback."""
    await cl.Message(content="👍 Təşəkkürlər! Rəyiniz qeydə alındı.").send()
    await action.remove()


@cl.action_callback("feedback_negative")
async def on_feedback_negative(action: cl.Action):
    """Handle negative feedback."""
    await cl.Message(content="👎 Rəyiniz qeydə alındı. Təkmilləşdirəcəyik.").send()
    await action.remove()


# ============================================
# AUDIO INPUT (Voice for Farmers)
# ============================================
# Farmers in the field can speak questions instead of typing.
# Uses browser's MediaRecorder to capture audio, then transcribes via Whisper.


@cl.on_audio_start
async def on_audio_start():
    """Called when user starts recording audio.

    Return True to allow recording, False to reject.
    We could add checks here (e.g., rate limiting).
    """
    logger.info("audio_recording_started")
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Process incoming audio chunks.

    For real-time transcription, we could accumulate chunks here.
    Currently we wait for the full recording (on_audio_end).
    """
    # Buffer chunks if needed for streaming transcription
    # For now, we do nothing - wait for complete audio in on_audio_end
    _ = chunk  # Mark as intentionally unused


@cl.on_audio_end
async def on_audio_end(elements: list[cl.Audio]):
    """Called when audio recording ends. Transcribe and process.

    Args:
        elements: List of Audio elements with the recorded audio
    """
    if not elements:
        logger.warning("audio_end_no_elements")
        return

    audio = elements[0]  # Get the first (and usually only) audio element

    # Show audio processing indicator
    thinking_msg = cl.Message(content=LoadingStates.transcribing_audio())
    await thinking_msg.send()

    try:
        # Get audio data
        audio_data = audio.content
        if not isinstance(audio_data, bytes):
            logger.error("audio_data_not_bytes", type=type(audio_data).__name__)
            await thinking_msg.remove()
            await cl.Message(content="❌ Audio formatı dəstəklənmir.").send()
            return
        mime_type = audio.mime or "audio/webm"

        logger.info(
            "audio_transcription_started",
            size_bytes=len(audio_data) if audio_data else 0,
            mime_type=mime_type,
        )

        # Transcribe using Whisper via Ollama or external service
        transcription = await transcribe_audio_whisper(audio_data, mime_type)

        if transcription and transcription.strip():
            # Remove thinking message
            await thinking_msg.remove()

            # Show transcribed text as user message
            await cl.Message(
                content=transcription,
                author="user",
            ).send()

            logger.info("audio_transcribed", text=transcription[:100])

            # Process as regular message
            msg = cl.Message(content=transcription)
            await on_message(msg)
        else:
            # Remove thinking message and show error
            await thinking_msg.remove()
            await cl.Message(
                content="❌ Səs aydın deyildi. Zəhmət olmasa yenidən cəhd edin."
            ).send()
            logger.warning("audio_transcription_empty")

    except Exception as e:  # noqa: BLE001
        logger.error("audio_transcription_error", error=str(e))
        await thinking_msg.remove()
        await cl.Message(content=f"❌ Xəta: {str(e)}").send()


async def transcribe_audio_whisper(audio_data: bytes, mime_type: str) -> str:
    """Transcribe audio using Whisper model.

    Options:
    1. Local Whisper via Ollama (if model available)
    2. OpenAI Whisper API (requires API key)
    3. Azure Speech Services (requires Azure subscription)

    For now, we use a simple approach with httpx to Ollama or fallback.

    Args:
        audio_data: Raw audio bytes
        mime_type: MIME type (e.g., "audio/webm", "audio/wav")

    Returns:
        Transcribed text string
    """
    import tempfile

    import httpx

    # Save audio to temp file (Whisper needs file input)
    ext = ".webm" if "webm" in mime_type else ".wav"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_data)
        temp_path = f.name

    try:
        # Try OpenAI-compatible Whisper endpoint (works with local or cloud)
        whisper_url = os.getenv("WHISPER_API_URL", "http://localhost:11434/v1/audio/transcriptions")
        whisper_key = os.getenv("WHISPER_API_KEY", "")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Method 1: OpenAI-compatible API (Ollama with whisper model)
            with open(temp_path, "rb") as audio_file:
                files = {"file": (f"audio{ext}", audio_file, mime_type)}
                data = {"model": "whisper", "language": "az"}  # Azerbaijani
                headers = {}
                if whisper_key:
                    headers["Authorization"] = f"Bearer {whisper_key}"

                response = await client.post(whisper_url, files=files, data=data, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.warning(
                        "whisper_api_error", status=response.status_code, detail=response.text[:200]
                    )

        # Fallback: Return placeholder if no Whisper available
        logger.warning("whisper_not_available", detail="No Whisper service configured")
        return ""

    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


# ============================================
# SESSION MANAGEMENT
# ============================================
@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with farm context, user tracking, ALEM persona, and dashboard welcome."""
    # Add image upload button for Vision-to-Action flow
    try:
        cl.UploadButton(
            name="image_uploads", multiple=True, accept=["image/png", "image/jpeg"]
        ).render()
        cl.user_session.set("uploaded_images", [])
    except Exception:
        pass
    session_id = cl.user_session.get("id")

    # Get authenticated user (if OAuth enabled)
    # This is the REAL user (developer/tester), separate from farmer profile
    user: cl.User | None = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    user_email = user.metadata.get("email") if user and user.metadata else None

    # ─────────────────────────────────────────────────────────────
    # ENSURE USER IS PERSISTED TO DB (CRITICAL!)
    # ─────────────────────────────────────────────────────────────
    # This MUST happen before creating personas or any related records
    # to avoid foreign key constraint violations
    if user:
        from data_layer import ensure_user_persisted

        user_persisted = await ensure_user_persisted(user)
        if not user_persisted:
            logger.warning(
                "user_not_persisted_continuing_anyway",
                user_id=user_id,
            )

    # ─────────────────────────────────────────────────────────────
    # JIT PERSONA PROVISIONING — Generate synthetic agricultural identity
    # ─────────────────────────────────────────────────────────────
    # This is the magic: even though the user logged in with minimal Google claims,
    # we first try to load an existing persona from DB, then auto-generate if missing.
    # This ensures the demo always has rich, personalized context that persists.
    alem_persona: ALEMPersona | None = None

    if user and user.metadata:
        # Extract OAuth claims from user metadata
        oauth_claims = {
            "name": user.metadata.get("name", "Unknown Farmer"),
            "email": user.metadata.get("email", user_email),
        }

        # Try to load existing persona from database
        existing_persona_dict = await load_alem_persona_from_db(email=user_email)

        if existing_persona_dict:
            # Persona exists - reconstruct ALEMPersona object
            alem_persona = ALEMPersona(
                user_id=user_id,
                full_name=existing_persona_dict["full_name"],
                email=existing_persona_dict["email"],
                fin_code=existing_persona_dict["fin_code"],
                phone=existing_persona_dict["phone"],
                region=existing_persona_dict["region"],
                crop_type=existing_persona_dict["crop_type"],
                total_area_ha=existing_persona_dict["total_area_ha"],
                experience_level=existing_persona_dict["experience_level"],
                ektis_verified=existing_persona_dict["ektis_verified"],
            )
            # Update last login time
            await update_persona_login_time(email=user_email)
            logger.info(
                "persona_loaded_from_db",
                user_id=user_id,
                fin_code=alem_persona.fin_code,
                region=alem_persona.region,
            )
        else:
            # No existing persona - generate new one
            alem_persona = PersonaProvisioner.provision_from_oauth(
                user_id=user_id,
                oauth_claims=oauth_claims,
                existing_persona=None,
            )
            # Save to database for next time
            await save_alem_persona_to_db(
                alem_persona=alem_persona.to_dict(),
                chainlit_user_id=user_id,
                email=user_email,
            )
            logger.info(
                "persona_generated_and_saved",
                user_id=user_id,
                fin_code=alem_persona.fin_code,
                region=alem_persona.region,
            )

        # Store in session for later use (context for expertise detection + prompts)
        # NOTE: NOT displayed in UI - farm context influences responses implicitly
        cl.user_session.set("alem_persona", alem_persona.to_dict())

        logger.info(
            "alem_persona_provisioned",
            user_id=user_id,
            fin_code=alem_persona.fin_code,
            region=alem_persona.region,
            crop_type=alem_persona.crop_type,
        )
    else:
        logger.debug("no_authenticated_user_skipping_persona")

    # ─────────────────────────────────────────────────────────────
    # SMART EXPERTISE DETECTION — Auto-detect from ALEM persona
    # ─────────────────────────────────────────────────────────────
    alem_persona_dict = cl.user_session.get("alem_persona")
    default_expertise = detect_expertise_from_persona(alem_persona_dict)

    # Build combined prompt from detected expertise
    profile_prompt = build_combined_system_prompt(default_expertise)

    logger.info(
        "expertise_detected",
        default_expertise=default_expertise,
        has_prompt=bool(profile_prompt),
    )

    # Store session info
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("user_email", user_email)
    cl.user_session.set("profile_prompt", profile_prompt)  # For system prompt enhancement
    cl.user_session.set("expertise_areas", default_expertise)  # For on_message handler
    cl.user_session.set("interaction_mode", "Ask")
    cl.user_session.set("llm_model", demo_settings.ollama_model)

    persona_crop = (
        alem_persona.crop_type
        if alem_persona
        else (alem_persona_dict.get("crop_type") if alem_persona_dict else None)
    )
    persona_region = (
        alem_persona.region
        if alem_persona
        else (alem_persona_dict.get("region") if alem_persona_dict else None)
    )

    logger.info(
        "expertise_configured",
        expertise=default_expertise,
        user_id=user_id,
        has_custom_prompt=bool(profile_prompt),
    )

    # Default farm for demo (synthetic farmer profile - NOT the real user)
    farm_id = "demo_farm_001"
    cl.user_session.set("farm_id", farm_id)

    # Store thread_id for LangGraph (use session_id for continuity)
    cl.user_session.set("thread_id", session_id)

    # Initialize Chat Settings (sidebar preferences panel)
    # Pass user so settings can be loaded from database (if data persistence enabled)
    user_settings = await setup_chat_settings(user=user)
    cl.user_session.set("user_preferences", user_settings)

    # Capture the active model for this session (stored for logging, not displayed to user)
    active_model = resolve_active_model()
    cl.user_session.set("active_model", active_model)
    # NOTE: Model info is intentionally NOT displayed to users
    # It's technical debug info that confuses the welcome experience
    # Developers can see it in startup banner or via /debug endpoint
    logger.debug(
        "active_model_configured",
        provider=active_model.get("provider"),
        model=active_model.get("model"),
        location=active_model.get("location"),
    )

    # Initialize LangGraph agent (Direct Mode - Simplified)
    checkpointer = await get_app_checkpointer()
    agent = compile_agent_graph(checkpointer=checkpointer)
    cl.user_session.set("agent", agent)
    logger.info(
        "session_started_direct_mode",
        session_id=session_id,
        user_id=user_id,
        farm_id=farm_id,
    )

    # ─────────────────────────────────────────────────────────────
    # THREAD METADATA PERSISTENCE (For Resume Functionality)
    # ─────────────────────────────────────────────────────────────
    # Store session state in thread metadata so it can be restored on resume
    data_layer = get_data_layer()
    if data_layer and user:
        try:
            # Get current thread (auto-created by Chainlit on first message)
            # We'll update its metadata on first message or here if possible
            thread_metadata = {
                "farm_id": farm_id,
                "expertise_areas": default_expertise,
                "alem_persona_fin": alem_persona_dict.get("fin_code")
                if alem_persona_dict
                else None,
                "language": "az",
                "active_model": active_model,
                "interaction_mode": "Ask",
                "llm_model": demo_settings.ollama_model,
            }
            cl.user_session.set("thread_metadata", thread_metadata)
            logger.debug("thread_metadata_prepared", metadata_keys=list(thread_metadata.keys()))
        except Exception as e:
            logger.warning("thread_metadata_preparation_failed", error=str(e))

    # Persist initial name/tags so the sidebar shows contextual chips immediately
    await update_thread_presentation(
        name=build_thread_name(persona_crop, persona_region, None),
        tags=build_thread_tags(
            persona_crop,
            persona_region,
            default_expertise,
            interaction_mode="Ask",
            llm_model=demo_settings.ollama_model,
        ),
        metadata_updates={
            **(cl.user_session.get("thread_metadata") or {}),
            "is_shared": False,
            "shared_at": None,
            "interaction_mode": "Ask",
            "llm_model": demo_settings.ollama_model,
        },
    )

    # ─────────────────────────────────────────────────────────────
    # WELCOME EXPERIENCE (Two-Part Strategy)
    # ─────────────────────────────────────────────────────────────
    # PART 1: Activity Dashboard (Sidebar) - Background context
    # PART 2: Welcome Message (Main Chat) - Primary interaction
    # See: DASHBOARD WELCOME comment block for full architecture
    # ─────────────────────────────────────────────────────────────
    try:
        insights_client = get_insights_client()
        if insights_client.is_configured:
            user_insights = await get_user_dashboard_data(user_id, days=90)
            cl.user_session.set("user_insights", user_insights)

            # PART 1: Render the activity dashboard in sidebar (non-intrusive)
            try:
                # Get persona and expertise for ALEM mirror
                alem_persona_dict = cl.user_session.get("alem_persona")
                expertise_areas = cl.user_session.get("expertise_areas")

                await render_dashboard_sidebar(
                    user_insights,
                    alem_persona=alem_persona_dict,
                    expertise_areas=expertise_areas,
                )
                logger.info(
                    "dashboard_sidebar_rendered",
                    user_id=user_id,
                    total_interactions=user_insights.total_interactions,
                    has_persona=bool(alem_persona_dict),
                )
            except Exception as e:
                logger.warning("dashboard_sidebar_render_failed", error=str(e), exc_info=True)
                # Continue anyway - sidebar failure shouldn't block chat

            logger.info(
                "dashboard_loaded",
                user_id=user_id,
                total_interactions=user_insights.total_interactions,
            )
        else:
            logger.debug("langfuse_not_configured_skipping_dashboard")
    except Exception as e:
        logger.warning("dashboard_load_failed", error=str(e), exc_info=True)

    # PART 2: Send the enhanced dashboard welcome message (main chat)
    # This is the PRIMARY user-facing welcome experience
    await send_dashboard_welcome(user)


# ============================================
# THREAD RESUME (Critical for UX!)
# ============================================
# This makes the thread list in sidebar functional.
# When user refreshes browser and clicks "Resume" → this restores session state.


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Resume existing thread after browser refresh.

    This is THE MISSING PIECE that makes threads work in UI!
    Without this, clicking "Resume Thread" does nothing.

    Args:
        thread: Contains id, name, userId, metadata, tags, createdAt
    """
    logger.info(
        "thread_resumed",
        thread_id=thread["id"],
        user_id=thread.get("userId"),
        thread_name=thread.get("name"),
    )

    # 1. Get authenticated user
    user: cl.User | None = cl.user_session.get("user")
    user_id = user.identifier if user else thread.get("userId", "anonymous")
    user_email = user.metadata.get("email") if user and user.metadata else None

    # 2. Restore session variables from thread metadata
    metadata = thread.get("metadata", {})
    # Chainlit can store thread metadata as a JSON string in some setups.
    # Normalize to dict to avoid AttributeError on .get()
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) if metadata.strip() else {}
        except Exception:
            metadata = {}
    cl.user_session.set("thread_id", thread["id"])
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("user_email", user_email)
    cl.user_session.set("farm_id", metadata.get("farm_id", "demo_farm_001"))

    # 3. Restore ALEM persona
    if user and user_email:
        from alem_persona_db import load_alem_persona_from_db, update_persona_login_time

        existing_persona_dict = await load_alem_persona_from_db(email=user_email)
        if existing_persona_dict:
            cl.user_session.set("alem_persona", existing_persona_dict)
            await update_persona_login_time(email=user_email)
            logger.info("persona_restored", fin_code=existing_persona_dict.get("fin_code"))
        else:
            logger.warning("persona_not_found_on_resume", email=user_email)

    # 4. Restore chat settings
    from data_layer import load_farm_scenario, load_user_settings

    user_settings = await load_user_settings(user)
    cl.user_session.set("user_preferences", user_settings)

    # 5. Restore farm scenario from database
    scenario = await load_farm_scenario(user_id=user_id, thread_id=thread["id"])
    if scenario:
        cl.user_session.set("scenario_context", scenario)
        cl.user_session.set("settings_version", scenario.get("settings_version", 1))
        logger.info(
            "scenario_restored",
            crop=scenario.get("specific_crop"),
            stage=scenario.get("conversation_stage"),
        )

    # 6. Restore expertise areas (from metadata or regenerate from persona)
    alem_persona_dict = cl.user_session.get("alem_persona")
    expertise = metadata.get("expertise_areas")
    if not expertise and alem_persona_dict:
        # Regenerate from persona if not in metadata
        expertise = detect_expertise_from_persona(alem_persona_dict)
    if not expertise:
        expertise = ["general"]
    cl.user_session.set("expertise_areas", expertise)

    # Build system prompt from expertise
    profile_prompt = build_combined_system_prompt(expertise)
    cl.user_session.set("profile_prompt", profile_prompt)

    # 7. Get active model metadata
    active_model = resolve_active_model()
    cl.user_session.set("active_model", active_model)

    # 8. Reinitialize LangGraph agent with SAME thread_id
    # This allows LangGraph to load conversation history from checkpoint
    checkpointer = await get_app_checkpointer()
    agent = compile_agent_graph(checkpointer=checkpointer)
    cl.user_session.set("agent", agent)

    # 9. Restore chat settings UI
    await setup_chat_settings(user=user)

    logger.info(
        "thread_resume_complete",
        thread_id=thread["id"],
        user_id=user_id,
        has_persona=bool(alem_persona_dict),
        has_settings=bool(user_settings),
        has_scenario=bool(scenario),
        expertise=expertise,
    )

    # 10. Send a subtle "conversation resumed" indicator
    await cl.Message(
        content="🔄 Söhbət bərpa olundu. Sualınızı davam etdirə bilərsiniz.",
        author="system",
    ).send()


# ============================================
# SHARED THREAD ACCESS (Sidebar "Share" button)
# ============================================


@cl.on_shared_thread_view
async def on_shared_thread_view(thread: ThreadDict, viewer: cl.User | None) -> bool:
    """Allow viewing shared threads (placeholder policy: allow all viewers)."""
    viewer_id = viewer.identifier if viewer else "anonymous"
    metadata = thread.get("metadata", {}) or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) if metadata.strip() else {}
        except Exception:
            metadata = {}
    logger.info(
        "shared_thread_view",
        thread_id=thread.get("id"),
        owner_id=thread.get("userId"),
        viewer_id=viewer_id,
        is_shared=metadata.get("is_shared"),
    )
    # Placeholder policy: always allow shared link viewers
    return True


# ============================================
# MESSAGE HANDLER
# ============================================
@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with dual-mode support.

    Supports two integration modes:
    - 'direct': In-process LangGraph execution (development)
    - 'api': HTTP calls to FastAPI graph API (production-like)

    Set via INTEGRATION_MODE environment variable.
    """
    # Get session data
    user_id = cl.user_session.get("user_id", "anonymous")
    farm_id = cl.user_session.get("farm_id")
    thread_id = cl.user_session.get("thread_id")

    # Get user preferences for response customization
    user_preferences = cl.user_session.get("user_preferences", {})
    enable_thinking_steps = user_preferences.get(
        "show_thinking_steps", demo_settings.enable_thinking_steps
    )
    enable_feedback = user_preferences.get("enable_feedback", demo_settings.enable_feedback)

    # Get expertise-enhanced system prompt
    profile_prompt = cl.user_session.get("profile_prompt", "")
    scenario_context = cl.user_session.get("scenario_context", None)

    logger.info(
        "message_received",
        user_id=user_id,
        message_length=len(message.content),
        has_profile_prompt=bool(profile_prompt),
        expertise_areas=cl.user_session.get("expertise_areas", []),
        integration_mode=demo_settings.integration_mode,
    )

    # Create response message
    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        # ═══════════════════════════════════════════════════════
        # ROUTE TO APPROPRIATE HANDLER BASED ON INTEGRATION MODE
        # ═══════════════════════════════════════════════════════

        if demo_settings.use_api_bridge:
            # ─────────────────────────────────────────────────────
            # API MODE — HTTP calls to FastAPI graph API
            # ─────────────────────────────────────────────────────
            await _handle_message_api_mode(
                message=message,
                response_msg=response_msg,
                user_id=user_id,
                farm_id=farm_id,
                thread_id=thread_id,
                profile_prompt=profile_prompt,
                scenario_context=scenario_context,
                enable_thinking_steps=enable_thinking_steps,
                enable_feedback=enable_feedback,
            )
        else:
            # ─────────────────────────────────────────────────────
            # DIRECT MODE — Native LangGraph Integration
            # ─────────────────────────────────────────────────────
            await _handle_message_direct_mode(
                message=message,
                response_msg=response_msg,
                user_id=user_id,
                thread_id=thread_id,
                profile_prompt=profile_prompt,
                scenario_context=scenario_context,
                enable_thinking_steps=enable_thinking_steps,
                enable_feedback=enable_feedback,
            )

    except Exception as e:
        logger.error("message_handler_error", error=str(e), exc_info=True)
        await response_msg.stream_token(f"\n\n❌ Gözlənilməz xəta: {str(e)}")
        await response_msg.update()


# ============================================
# API MODE HANDLER
# ============================================
async def _handle_message_api_mode(
    message: cl.Message,
    response_msg: cl.Message,
    user_id: str,
    farm_id: str | None,
    thread_id: str,
    profile_prompt: str,
    scenario_context: dict | None,
    enable_thinking_steps: bool,
    enable_feedback: bool,
):
    """Handle message via HTTP API calls to FastAPI graph routes.

    This mode mirrors production behavior - all graph execution happens
    in a separate FastAPI process, accessed via HTTP.
    """
    import httpx

    try:
        async with httpx.AsyncClient(
            base_url=demo_settings.yonca_api_url,
            timeout=120.0,
        ) as client:
            # Prepare request payload
            payload = {
                "message": message.content,
                "thread_id": thread_id,
                "user_id": user_id,
                "farm_id": farm_id,
                "language": "az",
                "system_prompt_override": profile_prompt if profile_prompt else None,
                "scenario_context": scenario_context,
            }

            # Call graph API
            logger.info(
                "calling_graph_api",
                endpoint=f"{demo_settings.yonca_api_url}/api/v1/graph/invoke",
                thread_id=thread_id,
            )

            response = await client.post(
                "/api/v1/graph/invoke",
                json=payload,
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            response_text = result.get("response", "")

            # Display response
            await response_msg.stream_token(response_text)

            logger.info(
                "message_processed_api",
                user_id=user_id,
                thread_id=thread_id,
                response_length=len(response_text),
            )

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        logger.error(
            "graph_api_error",
            status_code=e.response.status_code if e.response else None,
            detail=error_detail,
        )
        await response_msg.stream_token(
            f"\n\n❌ API xətası: {e.response.status_code if e.response else 'Unknown'}\n{error_detail}"
        )
    except httpx.RequestError as e:
        logger.error("graph_api_connection_error", error=str(e))
        await response_msg.stream_token(f"\n\n❌ API bağlantı xətası. FastAPI işləyir?\n{str(e)}")
    except Exception as e:
        logger.error("api_mode_error", error=str(e), exc_info=True)
        raise

    # Finalize response
    await response_msg.update()

    # Add feedback buttons if enabled
    if enable_feedback:
        await _add_feedback_buttons(response_msg)


# ============================================
# DIRECT MODE HANDLER
# ============================================
async def _handle_message_direct_mode(
    message: cl.Message,
    response_msg: cl.Message,
    user_id: str,
    thread_id: str,
    profile_prompt: str,
    scenario_context: dict | None,
    enable_thinking_steps: bool,
    enable_feedback: bool,
):
    """Handle message via in-process LangGraph execution.

    This is the original implementation - graph runs in the same
    process as Chainlit UI. Good for development, not scalable.
    """
    agent = cl.user_session.get("agent")
    model_info = cl.user_session.get("active_model") or resolve_active_model()

    if not agent:
        logger.error("agent_not_initialized")
        await response_msg.stream_token("❌ Agent yüklənməyib. Zəhmət olmasa səhifəni yeniləyin.")
        await response_msg.update()
        return

    # Configure LangGraph execution
    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
        },
        "metadata": {
            "model": model_info.get("model"),
            "provider": model_info.get("provider"),
            "location": model_info.get("location"),
            "integration_mode": model_info.get("integration_mode"),
            "source": model_info.get("source"),
            "base_url": model_info.get("base_url"),
        },
    }

    # Add Chainlit callback for native step visualization
    # Also add Langfuse callback for observability
    callbacks = []

    if enable_thinking_steps:
        # Chainlit's native LangChain callback handler
        # This automatically creates steps for LangGraph nodes
        cb = cl.LangchainCallbackHandler()
        callbacks.append(cb)

    # Add Langfuse tracing (always enabled for observability)
    try:
        from yonca.observability.langfuse import create_langfuse_handler

        langfuse_handler = create_langfuse_handler(
            session_id=thread_id,  # ✅ Maps to Langfuse session
            user_id=user_id,
            tags=["alem", "chat-ui", "direct-mode"],
            metadata={
                "model": model_info.get("model"),
                "provider": model_info.get("provider"),
                "has_profile": bool(profile_prompt),
            },
            trace_name=f"alem_chat_{thread_id[:8]}",
        )

        if langfuse_handler:
            callbacks.append(langfuse_handler)
            logger.debug("langfuse_handler_attached", thread_id=thread_id)
    except Exception as e:
        logger.warning("langfuse_handler_failed", error=str(e))

    if callbacks:
        config["callbacks"] = callbacks

    # Prepare initial state with profile-specific system prompt
    from yonca.agent.state import create_initial_state

    initial_state = create_initial_state(
        thread_id=thread_id,
        user_input=message.content,
        user_id=user_id,
        language="az",
        system_prompt_override=profile_prompt if profile_prompt else None,
        scenario_context=scenario_context,
    )

    # Stream response from LangGraph with step visualization
    try:
        # Import step visualization utilities
        from services.step_visualization import (
            _summarize_node_output,
            create_step_for_node,
            update_step_output,
        )

        current_step = None

        async for event in agent.astream(initial_state, config=config):
            # Extract response from final state
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    # Create step visualization if enabled
                    if enable_thinking_steps and node_name != "__start__":
                        # Close previous step if exists
                        if current_step:
                            try:
                                summary = _summarize_node_output(node_name, node_output)
                                await update_step_output(current_step, summary, "done")
                            except Exception as e:
                                logger.warning("step_update_failed", node=node_name, error=str(e))

                        # Create new step for current node
                        try:
                            current_step = await create_step_for_node(node_name)
                        except Exception as e:
                            logger.warning("step_creation_failed", node=node_name, error=str(e))
                            current_step = None

                    # Check for response content
                    if "current_response" in node_output:
                        response_content = node_output["current_response"]
                        await response_msg.stream_token(response_content)

                    # Log node execution
                    logger.debug(
                        "node_executed",
                        node=node_name,
                        has_response="current_response" in node_output,
                    )

        # Close final step
        if current_step and enable_thinking_steps:
            try:
                await update_step_output(current_step, "✓ Tamamlandı", "done")
            except Exception:
                pass

        logger.info(
            "message_processed_direct",
            user_id=user_id,
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error("langgraph_execution_error", error=str(e), exc_info=True)
        await response_msg.stream_token(f"\n\n❌ Xəta: {str(e)}")

    # Finalize response
    await response_msg.update()

    # Add feedback buttons if enabled
    if enable_feedback:
        await _add_feedback_buttons(response_msg)


# ============================================
# SHARED UTILITIES
# ============================================
async def _add_feedback_buttons(response_msg: cl.Message):
    """Add feedback action buttons to a message."""
    actions = [
        cl.Action(
            name="feedback_positive",
            value="positive",
            label="👍 Kömək etdi",
            payload={"type": "feedback", "sentiment": "positive"},
        ),
        cl.Action(
            name="feedback_negative",
            value="negative",
            label="👎 Təkmilləşdirmək olar",
            payload={"type": "feedback", "sentiment": "negative"},
        ),
    ]
    await response_msg.send()
    for action in actions:
        await action.send(for_id=response_msg.id)


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import chainlit.cli

    chainlit.cli.run_chainlit(__file__)
