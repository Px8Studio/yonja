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

import os
import sys
from pathlib import Path
from typing import Optional

# Load .env files BEFORE any other imports
from dotenv import load_dotenv

demo_ui_dir = Path(__file__).parent
project_root = demo_ui_dir.parent
load_dotenv(project_root / ".env")
load_dotenv(demo_ui_dir / ".env")

sys.path.insert(0, str(project_root / "src"))

# ============================================
# CHAINLIT DATA LAYER INITIALIZATION (CRITICAL)
# ============================================
# Must happen BEFORE importing chainlit to prevent "storage client not initialized" warning
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from chainlit.data.chainlit_data_layer import ChainlitDataLayer  # noqa: E402
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer  # noqa: E402
import logging

logger = logging.getLogger(__name__)

async def init_chainlit_data_layer():
    """Initialize Chainlit's SQLAlchemy data layer with async engine."""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/yonca.db")
        logger.info(f"Initializing Chainlit data layer with: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        
        # Create async engine
        engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Create async session factory
        async_session_maker = sessionmaker(
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

# Initialize before importing chainlit
try:
    asyncio.run(init_chainlit_data_layer())
except Exception as e:
    logger.error(f"Failed to initialize data layer: {e}")

# Now safe to import chainlit
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider, MultiSelect
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
import structlog

# Import from main yonca package (for direct mode)
from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer_async
from yonca.observability import create_langfuse_handler
from yonca.observability.banner import (
    print_startup_banner,
    print_section_header,
    print_status_line,
    print_endpoints,
    print_quick_links,
    print_startup_complete,
    print_llm_info,
    print_model_capabilities,
    print_infrastructure_tier,
)

# Import demo-ui config and API client
from config import settings as demo_settings
from services.yonca_client import YoncaClient, YoncaClientError
from data_layer import get_data_layer, load_user_settings, save_user_settings
from alem_persona import ALEMPersona, PersonaProvisioner
from alem_persona_db import (
    load_alem_persona_from_db,
    save_alem_persona_to_db,
    update_persona_login_time,
)

# Import insights dashboard components
from services.langfuse_insights import (
    get_insights_client,
    get_response_metadata,
    get_user_dashboard_data,
)
from components.insights_dashboard import (
    format_response_metadata,
    add_response_metadata_element,
    render_dashboard_sidebar,
    format_welcome_stats,
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
        demo_settings.llm_provider, 
        (demo_settings.llm_provider, "")
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

redis_host = demo_settings.redis_url.replace("redis://", "").split("/")[0] if demo_settings.redis_url else "not configured"
redis_db = demo_settings.redis_url.split("/")[-1] if "/" in demo_settings.redis_url else "0"
print_status_line("Redis", f"localhost:{redis_host.split(':')[-1]}/db{redis_db}", "success", "LangGraph checkpointing")

if demo_settings.data_persistence_enabled:
    db_host = demo_settings.effective_database_url.split("@")[-1].split("/")[0] if "@" in demo_settings.effective_database_url else "local"
    db_name = demo_settings.effective_database_url.split("/")[-1].split("?")[0] if "/" in demo_settings.effective_database_url else "yonca"
    print_status_line("PostgreSQL", f"{db_host}/{db_name}", "success", "users, threads, settings")
else:
    print_status_line("PostgreSQL", "Not configured", "warning", "sessions not persisted")

# ─────────────────────────────────────────────────────────────
# Features
# ─────────────────────────────────────────────────────────────
print_section_header("✨ Features")
print_status_line("OAuth", "Enabled" if demo_settings.oauth_enabled else "Disabled", "success" if demo_settings.oauth_enabled else "info", "Google login" if demo_settings.oauth_enabled else "anonymous mode")
print_status_line("Farm Selector", "Enabled" if demo_settings.enable_farm_selector else "Disabled", "success" if demo_settings.enable_farm_selector else "info")
print_status_line("Thinking Steps", "Enabled" if demo_settings.enable_thinking_steps else "Disabled", "success" if demo_settings.enable_thinking_steps else "info", "shows agent reasoning")
print_status_line("Feedback", "Enabled" if demo_settings.enable_feedback else "Disabled", "success" if demo_settings.enable_feedback else "info", "👍/👎 buttons")

# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────
print_endpoints([
    ("Chat UI", "http://localhost:8501", "Interactive Chainlit demo"),
    ("Swagger", "http://localhost:8000/docs", "Interactive API docs"),
    ("ReDoc", "http://localhost:8000/redoc", "Clean API reference"),
    ("Health", "http://localhost:8000/health", "Readiness & liveness probes"),
    ("Langfuse UI", "http://localhost:3001", "LLM tracing & analytics dashboard"),
    ("Langfuse API", "http://localhost:3001/api/public", "Langfuse Public API"),
    ("LangGraph API", "http://127.0.0.1:2024", "LangGraph development server"),
    ("LangGraph Docs", "http://127.0.0.1:2024/docs", "LangGraph API documentation"),
])

print_quick_links([
    ("Chat", "http://localhost:8501"),
    ("Swagger", "http://localhost:8000/docs"),
    ("ReDoc", "http://localhost:8000/redoc"),
    ("Traces", "http://localhost:3001/traces"),
    ("LangGraph", "http://127.0.0.1:2024"),
    ("Studio", "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"),
])

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
if demo_settings.enable_data_persistence and demo_settings.data_persistence_enabled:
    @cl.data_layer
    def _get_data_layer():
        """Register Chainlit data layer for persistence."""
        return get_data_layer()

# Global checkpointer (initialized once in async context) - for direct mode
_checkpointer = None

# Global API client (for API bridge mode)
_api_client: YoncaClient | None = None


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
        cl.Starter(label="📅 Həftəlik plan", message="Bu həftə üçün iş planı hazırla", icon="/public/elements/calendar.svg"),
        cl.Starter(label="🌤️ Hava proqnozu", message="Bu günkü hava proqnozu necədir?", icon="/public/elements/weather.svg"),
        cl.Starter(label="💧 Suvarma vaxtı", message="Sahəmi nə vaxt suvarmalıyam?", icon="/public/elements/water.svg"),
        cl.Starter(label="💰 Subsidiyalar", message="Hansı subsidiyalardan yararlana bilərəm?", icon="/public/elements/money.svg"),
    ],
    "cotton": [
        cl.Starter(label="🌱 Pambıq əkini", message="Pambıq əkini üçün ən yaxşı vaxt nədir?", icon="/public/elements/plant.svg"),
        cl.Starter(label="🐛 Pambıq zərərvericisi", message="Pambıqda hansı zərərvericilər var?", icon="/public/elements/bug.svg"),
        cl.Starter(label="💧 Pambıq suvarması", message="Pambıq üçün suvarma norması nə qədərdir?", icon="/public/elements/water.svg"),
        cl.Starter(label="🧪 Pambıq gübrəsi", message="Pambıq üçün hansı gübrələr lazımdır?", icon="/public/elements/fertilizer.svg"),
    ],
    "wheat": [
        cl.Starter(label="🌾 Buğda əkini", message="Payızlıq buğda nə vaxt əkilir?", icon="/public/elements/wheat.svg"),
        cl.Starter(label="🌡️ Don zədəsi", message="Buğdanı dondan necə qorumaq olar?", icon="/public/elements/frost.svg"),
        cl.Starter(label="🌿 Alaq otları", message="Buğdada alaq otlarına qarşı nə etmək olar?", icon="/public/elements/weed.svg"),
        cl.Starter(label="📊 Buğda məhsuldarlığı", message="Buğda məhsuldarlığını necə artırmaq olar?", icon="/public/elements/chart.svg"),
    ],
    "orchard": [
        cl.Starter(label="🍎 Alma bağı", message="Alma ağaclarının qulluğu necə olmalıdır?", icon="/public/elements/apple.svg"),
        cl.Starter(label="🍇 Üzüm bağı", message="Üzüm bağının budaması nə vaxt olmalıdır?", icon="/public/elements/grape.svg"),
        cl.Starter(label="🌸 Çiçəklənmə", message="Meyvə ağaclarının çiçəklənmə dövrü nə vaxtdır?", icon="/public/elements/flower.svg"),
        cl.Starter(label="🪲 Meyvə zərərvericisi", message="Meyvə ağaclarında hansı zərərvericilər var?", icon="/public/elements/bug.svg"),
    ],
    "vegetable": [
        cl.Starter(label="🍅 Pomidor əkini", message="Pomidor əkini üçün torpaq necə hazırlanır?", icon="/public/elements/tomato.svg"),
        cl.Starter(label="🥒 Xıyar becərilməsi", message="Xıyar becərilməsinin sirləri nədir?", icon="/public/elements/cucumber.svg"),
        cl.Starter(label="🌶️ İstixana", message="İstixanada tərəvəz yetişdirmək necə olur?", icon="/public/elements/greenhouse.svg"),
        cl.Starter(label="🥔 Kartof əkini", message="Kartof əkini üçün ən yaxşı vaxt nə vaxtdır?", icon="/public/elements/potato.svg"),
    ],
    "livestock": [
        cl.Starter(label="🐄 Mal-qara", message="Mal-qaranın yemləmə rejimi necə olmalıdır?", icon="/public/elements/cow.svg"),
        cl.Starter(label="🐑 Qoyun", message="Qoyunların sağlamlığı üçün nə etmək lazımdır?", icon="/public/elements/sheep.svg"),
        cl.Starter(label="🐝 Arıçılıq", message="Arı ailələrinin qışlaması necə təşkil olunur?", icon="/public/elements/bee.svg"),
        cl.Starter(label="🏥 Baytarlıq", message="Heyvanların peyvəndləmə cədvəli necədir?", icon="/public/elements/vet.svg"),
    ],
    "advanced": [
        cl.Starter(label="📊 Torpaq analizi", message="Torpaq analizinin nəticələrini şərh et", icon="/public/elements/soil.svg"),
        cl.Starter(label="🔬 Xəstəlik diaqnozu", message="Bu bitkidə hansı xəstəlik var?", icon="/public/elements/microscope.svg"),
        cl.Starter(label="📈 ROI hesablaması", message="Əkin planımın rentabelliyini hesabla", icon="/public/elements/calculator.svg"),
        cl.Starter(label="🗺️ Peyk məlumatları", message="Sahəmin NDVI peyk şəkillərini göstər", icon="/public/elements/satellite.svg"),
    ],
}

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
# STARTERS (Context-aware conversation prompts)
# ============================================
# Starters are displayed based on expertise areas selected in Chat Settings.
# No separate profile dropdown - expertise is managed in one place only.

@cl.set_starters
async def set_starters(current_user: cl.User = None):
    """Return starters based on expertise areas from settings.
    
    Combines starters from all selected expertise areas.
    Defaults to 'general' if no expertise selected.
    """
    # Get expertise areas from user session settings
    # Use try-except to handle context not available yet
    try:
        settings = cl.user_session.get("chat_settings", {})
    except Exception:
        # Context not available yet, use empty settings
        settings = {}
    expertise_areas = settings.get("expertise_areas", [])
    
    if expertise_areas:
        # Combine starters from all selected expertise areas
        starters = []
        seen_labels = set()
        
        for area in expertise_areas:
            if area in PROFILE_STARTERS:
                for starter in PROFILE_STARTERS[area]:
                    # Avoid duplicates by label
                    if starter.label not in seen_labels:
                        starters.append(starter)
                        seen_labels.add(starter.label)
        
        # Return up to 6 most relevant starters
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
    return bool(
        os.getenv("OAUTH_GOOGLE_CLIENT_ID") and 
        os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")
    )


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
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.warning(
                    "people_api_error",
                    status=response.status_code,
                    detail=response.text[:200]
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
            
            logger.info(
                "people_api_success",
                fields_retrieved=list(result.keys())
            )
            
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
        _id_token: Optional[str] = None,
    ) -> Optional[cl.User]:
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
            given_name = raw_user_data.get("given_name")      # First name
            family_name = raw_user_data.get("family_name")    # Last name  
            locale = raw_user_data.get("locale")              # Language/region (e.g., "en", "az")
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
                    "image": picture,      # Chainlit expects 'image' for avatar
                    "picture": picture,    # Keep 'picture' too for compatibility
                    "provider": provider_id,
                    "google_id": google_id,
                    
                    # Profile details (profile scope - FREE)
                    "given_name": given_name,
                    "family_name": family_name,
                    "locale": locale,  # Language/region: "az", "en", "ru"
                    
                    # Organization (FREE - only for Google Workspace accounts)
                    "hosted_domain": hosted_domain,  # e.g., "zekalab.com"
                }
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
    "weather": "🌤️ Hava",
    "subsidy": "📋 Subsidiya",
    "irrigation": "💧 Suvarma",
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
async def setup_chat_settings(user: Optional[cl.User] = None):
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
    
    language_idx = language_values.index(persisted.get("language", "Azərbaycanca")) if persisted.get("language") in language_values else 0
    detail_idx = detail_values.index(persisted.get("detail_level", "Orta")) if persisted.get("detail_level") in detail_values else 1
    units_idx = unit_values.index(persisted.get("units", "Metrik (ha, kg)")) if persisted.get("units") in unit_values else 0
    currency_idx = currency_values.index(persisted.get("currency", "₼ AZN (Manat)")) if persisted.get("currency") in currency_values else 0
    
    settings = await cl.ChatSettings(
        [
            # ─────────────────────────────────────────────────────────────
            # EXPERTISE AREAS — Multi-select with smart defaults
            # ─────────────────────────────────────────────────────────────
            MultiSelect(
                id="expertise_areas",
                label="🧠 Ekspertiza sahələri",
                values=[label for _, label in expertise_values],
                initial_value=[
                    label for area_id, label in expertise_values
                    if area_id in expertise_areas
                ],
                description="Hansı sahələrdə məsləhət almaq istəyirsiniz? (Birdən çox seçə bilərsiniz)",
            ),
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
        ]
    ).send()
    
    # Store expertise areas in session for starters and prompts
    cl.user_session.set("chat_settings", {
        **persisted,
        "expertise_areas": expertise_areas,
    })
    
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
    
    Special handling for expertise_areas:
    - Converts labels back to IDs for internal use
    - Updates system prompt based on selected areas
    """
    user: Optional[cl.User] = cl.user_session.get("user")
    
    # ─────────────────────────────────────────────────────────────
    # PROCESS EXPERTISE AREAS — Convert labels to IDs
    # ─────────────────────────────────────────────────────────────
    raw_expertise = settings.get("expertise_areas", [])
    
    # Convert labels to IDs
    expertise_ids = []
    for label in raw_expertise:
        if label in EXPERTISE_LABEL_TO_ID:
            expertise_ids.append(EXPERTISE_LABEL_TO_ID[label])
        elif label in EXPERTISE_AREAS:  # Already an ID
            expertise_ids.append(label)
    
    # Store normalized settings with IDs
    normalized_settings = {
        **settings,
        "expertise_areas": expertise_ids,
    }
    
    logger.info(
        "settings_updated",
        session_id=cl.user_session.get("id"),
        user=user.identifier if user else "anonymous",
        raw_expertise=raw_expertise,
        expertise_ids=expertise_ids,
        settings={k: v for k, v in normalized_settings.items() if k != "expertise_areas"},
    )
    
    # Update session with normalized settings
    cl.user_session.set("chat_settings", normalized_settings)
    
    # Build combined system prompt based on expertise areas
    combined_prompt = build_combined_system_prompt(expertise_ids)
    cl.user_session.set("profile_prompt", combined_prompt)
    
    # Persist settings to database if user is authenticated
    if user:
        saved = await save_user_settings(user, normalized_settings)
        if saved:
            logger.info("settings_persisted", user=user.identifier)
    
    # Acknowledge the change to user with expertise summary
    language = settings.get("language", "Azərbaycanca")
    
    if expertise_ids:
        expertise_names = [EXPERTISE_AREAS.get(e, e) for e in expertise_ids]
        expertise_summary = ", ".join(expertise_names)
    else:
        expertise_summary = "Ümumi"
    
    if language == "English":
        await cl.Message(
            content=f"✅ Settings updated. Expertise areas: {expertise_summary}"
        ).send()
    elif language == "Русский":
        await cl.Message(
            content=f"✅ Настройки обновлены. Области экспертизы: {expertise_summary}"
        ).send()
    else:
        await cl.Message(
            content=f"✅ Parametrlər yeniləndi. Ekspertiza sahələri: {expertise_summary}"
        ).send()

# ============================================
# DASHBOARD WELCOME (Agricultural Command Center)
# ============================================
# BRANDING NOTE: Use "ALEM" as primary agent name. "Yonca" is the internal project name.
# AVOID: "Sidecar" (internal term), "DigiRella", "ZekaLab" (business names)
# ============================================
async def send_dashboard_welcome(user: Optional[cl.User] = None):
    """Send enhanced dashboard welcome with farm status and quick actions.
    
    Creates a "Warm Handshake" experience that transforms the chat from
    a generic interface into an agricultural command center.
    
    Args:
        user: Optional authenticated user for personalization
    """
    # Personalized greeting
    if user and user.metadata:
        user_name = user.metadata.get("name", "").split()[0]  # First name
        greeting = f"Salam, **{user_name}**! 👋"
    else:
        greeting = "Xoş gəlmisiniz! 👋"
    
    # Build compact dashboard message
    # Avatar is now shown via Chainlit's native avatar system (public/avatars/yonca_ai.svg)
    dashboard_content = f"""{greeting}

<div style="display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: linear-gradient(135deg, rgba(45, 90, 39, 0.06) 0%, rgba(168, 230, 207, 0.12) 100%); border-radius: 12px; margin: 8px 0;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="width: 10px; height: 10px; background: #4CAF50; border-radius: 50%; box-shadow: 0 0 6px rgba(76, 175, 80, 0.5);"></span>
        <span style="color: #2D5A27; font-weight: 500;">{AZ_STRINGS["status_normal"]}</span>
    </div>
    <span style="color: #999;">•</span>
    <span style="color: #666; font-size: 0.9em;">✓ {AZ_STRINGS["sima_auth"]}</span>
</div>

Mən sizin virtual aqronomam — əkin, suvarma və subsidiya məsələlərində kömək edirəm.
"""

    # Create quick action buttons using Chainlit Actions
    actions = [
        cl.Action(
            name="weather",
            payload={"action": "weather"},
            label=AZ_STRINGS["weather"],
        ),
        cl.Action(
            name="subsidy",
            payload={"action": "subsidy"},
            label=AZ_STRINGS["subsidy"],
        ),
        cl.Action(
            name="irrigation",
            payload={"action": "irrigation"},
            label=AZ_STRINGS["irrigation"],
        ),
    ]
    
    # Send the dashboard welcome message
    await cl.Message(
        content=dashboard_content,
        author="ALEM",
        actions=actions,
    ).send()


# ============================================
# NATIVE CHAINLIT ARCHITECTURE NOTE
# ============================================
# ✅ QUICK ACTIONS: Use @cl.set_starters (profile-aware)
# ✅ NOT: Custom @cl.action_callback (outdated pattern)
#
# Why? Starters are:
# - Profile-aware (cotton specialists see different actions)
# - Better UX (clear visual affordance)
# - Chainlit-native (not custom UI code)
#
# When user clicks starter → Message sent → @on_message handles it
# No separate action callbacks needed!
#
# See: CHAINLIT-NATIVE-ARCHITECTURE.md for full architecture
# ============================================


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
    
    # Show thinking indicator
    thinking_msg = cl.Message(content="🎤 Səsinizi eşidirəm...")
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
            mime_type=mime_type
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
            await cl.Message(content="❌ Səs aydın deyildi. Zəhmət olmasa yenidən cəhd edin.").send()
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
    import httpx
    import tempfile
    
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
                
                response = await client.post(
                    whisper_url,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "")
                else:
                    logger.warning(
                        "whisper_api_error",
                        status=response.status_code,
                        detail=response.text[:200]
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
    session_id = cl.user_session.get("id")
    
    # Get authenticated user (if OAuth enabled)
    # This is the REAL user (developer/tester), separate from farmer profile
    user: Optional[cl.User] = cl.user_session.get("user")
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
    alem_persona: Optional[ALEMPersona] = None
    
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
                full_name=existing_persona_dict['full_name'],
                email=existing_persona_dict['email'],
                fin_code=existing_persona_dict['fin_code'],
                phone=existing_persona_dict['phone'],
                region=existing_persona_dict['region'],
                crop_type=existing_persona_dict['crop_type'],
                total_area_ha=existing_persona_dict['total_area_ha'],
                experience_level=existing_persona_dict['experience_level'],
                ektis_verified=existing_persona_dict['ektis_verified'],
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
    
    # Initialize based on integration mode
    if demo_settings.use_api_bridge:
        # API Bridge Mode: Use YoncaClient to talk to FastAPI
        # This is the EXACT pattern Digital Umbrella will use
        api_client = await get_api_client()
        cl.user_session.set("api_client", api_client)
        logger.info(
            "session_started_api_mode",
            session_id=session_id,
            user_id=user_id,
            api_url=demo_settings.yonca_api_url,
        )
    else:
        # Direct Mode: Import LangGraph directly (faster for development)
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
    # Load Activity Dashboard (from Langfuse)
    # ─────────────────────────────────────────────────────────────
    try:
        insights_client = get_insights_client()
        if insights_client.is_configured:
            user_insights = await get_user_dashboard_data(user_id, days=90)
            cl.user_session.set("user_insights", user_insights)
            
            # Render the activity dashboard in sidebar
            await render_dashboard_sidebar(user_insights)
            
            logger.info(
                "dashboard_loaded",
                user_id=user_id,
                total_interactions=user_insights.total_interactions,
            )
        else:
            logger.debug("langfuse_not_configured_skipping_dashboard")
    except Exception as e:
        logger.warning("dashboard_load_failed", error=str(e))
    
    # Build the enhanced dashboard welcome message
    await send_dashboard_welcome(user)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with dual-mode support.
    
    - API Mode: Routes through FastAPI backend (production pattern)
    - Direct Mode: Calls LangGraph directly (development pattern)
    """
    session_id = cl.user_session.get("id")
    farm_id = cl.user_session.get("farm_id", "demo_farm_001")
    thread_id = cl.user_session.get("thread_id", session_id)
    user_id = cl.user_session.get("user_id", "anonymous")
    user_email = cl.user_session.get("user_email")
    
    # Get expertise-based profile prompt for specialized responses
    expertise_areas = cl.user_session.get("expertise_areas", ["general"])
    profile_prompt = cl.user_session.get("profile_prompt", "")
    
    # Create response message for streaming
    response_msg = cl.Message(content="", author="ALEM")
    await response_msg.send()
    
    full_response = ""
    
    try:
        if demo_settings.use_api_bridge:
            # ═══════════════════════════════════════════════════════
            # API BRIDGE MODE - The "Gold Standard" Production Pattern
            # This is EXACTLY how Digital Umbrella's mobile app will work
            # ═══════════════════════════════════════════════════════
            api_client = cl.user_session.get("api_client")
            if not api_client:
                api_client = await get_api_client()
                cl.user_session.set("api_client", api_client)
            
            # Show thinking indicator
            await response_msg.stream_token("🔄 ")
            
            try:
                # Call FastAPI backend - same as mobile app will
                result = await api_client.chat(
                    message=message.content,
                    session_id=thread_id,
                    farm_id=farm_id,
                    user_id=user_id,
                )
                full_response = result.content
                
                # Clear thinking indicator and show response
                response_msg.content = full_response
                await response_msg.update()
                
                logger.info(
                    "api_response_received",
                    session_id=session_id,
                    model=result.model,
                    tokens=result.tokens_used,
                    message_count=result.message_count,
                )
                
            except YoncaClientError as e:
                logger.error("api_error", error=str(e), status_code=e.status_code)
                response_msg.content = f"❌ API xətası: {e}"
                await response_msg.update()
                return
            
        else:
            # ═══════════════════════════════════════════════════════
            # DIRECT MODE - Fast Development Pattern
            # Calls LangGraph directly without HTTP overhead
            # ═══════════════════════════════════════════════════════
            agent = cl.user_session.get("agent")
            
            if not agent:
                checkpointer = await get_app_checkpointer()
                agent = compile_agent_graph(checkpointer=checkpointer)
                cl.user_session.set("agent", agent)
            
            # Build input for the agent
            input_messages = {
                "messages": [HumanMessage(content=message.content)]
            }
            
            # Create Langfuse handler for observability
            alem_persona_dict = cl.user_session.get("alem_persona", {})
            
            # Build tags with persona information
            tags = [
                "demo-ui",
                "development",
                "direct-mode",
                f"expertise:{','.join(expertise_areas)}",
            ]
            if alem_persona_dict:
                tags.extend([
                    f"fin:{alem_persona_dict.get('fin_code', 'unknown')}",
                    f"region:{alem_persona_dict.get('region', 'unknown')}",
                    f"crop:{alem_persona_dict.get('crop_type', 'unknown')}",
                    f"experience:{alem_persona_dict.get('experience_level', 'unknown')}",
                ])
            
            langfuse_handler = create_langfuse_handler(
                session_id=thread_id,           # Groups all messages in conversation
                user_id=user_id,                # Attributes costs to user
                tags=tags,
                metadata={
                    "farm_id": farm_id,
                    "user_email": user_email,
                    "source": "chainlit",
                    "expertise_areas": expertise_areas,
                    "alem_persona": alem_persona_dict,  # Full persona for analysis
                },
            )
            
            # Combine BOTH callback handlers
            callbacks = [cl.LangchainCallbackHandler()]  # UI step visualization
            if langfuse_handler:
                callbacks.append(langfuse_handler)        # LLM tracing
            
            # Pass to LangGraph
            config = RunnableConfig(
                configurable={"thread_id": thread_id},
                callbacks=callbacks  # Both handlers receive all events
            )
            
            # Stream the response from LangGraph
            # astream() returns an async generator - iterate with async for
            async for chunk in agent.astream(input_messages, config=config):
                # Extract content from the chunk based on its structure
                if isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        if isinstance(node_output, dict) and "messages" in node_output:
                            for msg in node_output["messages"]:
                                if hasattr(msg, "content") and msg.content:
                                    # Only update if we got actual content
                                    full_response = msg.content
            
            # Update final message with complete response
            response_msg.content = full_response
            await response_msg.update()
            
            # ─────────────────────────────────────────────────────────
            # Add Response Metadata (expandable details)
            # ─────────────────────────────────────────────────────────
            if langfuse_handler:
                try:
                    # Get trace_id from the handler (last_trace_id in SDK v3)
                    trace_id = getattr(langfuse_handler, 'last_trace_id', None) or \
                               getattr(langfuse_handler, 'trace_id', None)
                    if trace_id:
                        # Fetch metadata from Langfuse
                        metadata = await get_response_metadata(trace_id)
                        if metadata:
                            await add_response_metadata_element(response_msg, metadata)
                            logger.debug("response_metadata_added", trace_id=trace_id)
                except Exception as e:
                    logger.warning("response_metadata_failed", error=str(e))
        
    except Exception as e:
        logger.error("message_error", error=str(e), session_id=session_id)
        response_msg.content = AZ_STRINGS["error"]
        await response_msg.update()
        raise
    
    logger.info(
        "message_handled",
        session_id=session_id,
        mode="api" if demo_settings.use_api_bridge else "direct",
        user_message_length=len(message.content),
        response_length=len(full_response),
    )


@cl.on_stop
async def on_stop():
    """Handle user stopping generation."""
    logger.info("generation_stopped", session_id=cl.user_session.get("id"))


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)
