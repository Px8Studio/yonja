# demo-ui/app.py
"""Yonca AI Demo — Chainlit Application.

This is the main Chainlit application that provides a demo UI
for the Yonca AI agricultural assistant using native LangGraph integration.

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

# Load .env from demo-ui folder BEFORE any other imports
# This ensures OAuth secrets are available for Chainlit
from dotenv import load_dotenv
demo_ui_dir = Path(__file__).parent
load_dotenv(demo_ui_dir / ".env")  # Local secrets (gitignored)

# Add project root to path for imports
project_root = demo_ui_dir.parent
sys.path.insert(0, str(project_root / "src"))

# Now safe to import chainlit
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider
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
    ("Langfuse", "http://localhost:3001", "LLM tracing & analytics"),
])

print_quick_links([
    ("Chat", "http://localhost:8501"),
    ("Swagger", "http://localhost:8000/docs"),
    ("ReDoc", "http://localhost:8000/redoc"),
    ("Traces", "http://localhost:3001"),
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
    """Get or create the checkpointer singleton (async) - for direct mode."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await get_checkpointer_async(redis_url=demo_settings.redis_url)
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

def is_oauth_enabled() -> bool:
    """Check if OAuth is configured."""
    return bool(
        os.getenv("OAUTH_GOOGLE_CLIENT_ID") and 
        os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")
    )


# Only register OAuth callback if credentials are configured
# This prevents Chainlit from requiring OAuth env vars at startup
if is_oauth_enabled():
    @cl.oauth_callback
    async def oauth_callback(
        provider_id: str,
        _token: str,
        raw_user_data: dict[str, str],
        default_user: cl.User,
        _id_token: Optional[str] = None,
    ) -> Optional[cl.User]:
        """Handle OAuth callback from Google.
        
        This allows any authenticated Google user to access the demo.
        The user's email is stored and passed to Langfuse for tracking.
        
        Args:
            provider_id: OAuth provider (e.g., "google")
            _token: OAuth access token (unused but required by signature)
            raw_user_data: User info from provider
            default_user: Chainlit's default user object
            _id_token: Optional ID token (unused but required by signature)
            
        Returns:
            cl.User if allowed, None to deny access.
        """
        if provider_id == "google":
            # Extract user info
            email = raw_user_data.get("email", "unknown")
            name = raw_user_data.get("name", email)
            picture = raw_user_data.get("picture")
            
            logger.info(
                "oauth_login",
                provider=provider_id,
                email=email,
                name=name,
            )
            
            # Return user with metadata for Langfuse
            return cl.User(
                identifier=email,
                metadata={
                    "name": name,
                    "email": email,
                    "picture": picture,
                    "provider": provider_id,
                }
            )
        
        # Allow other providers with default user
        return default_user

# ============================================
# LOCALIZATION
# ============================================
AZ_STRINGS = {
    "welcome": "🌾 **Yonca AI Köməkçisinə xoş gəlmisiniz!**\n\nMən sizin virtual aqronomam. Əkin, suvarma, gübrələmə və digər kənd təsərrüfatı məsələlərində kömək edə bilərəm.",
    "farm_loaded": "📍 Təsərrüfat məlumatları yükləndi",
    "thinking": "Düşünürəm...",
    "error": "❌ Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.",
    "select_farm": "Təsərrüfat seçin",
    # Dashboard strings
    "farm_status": "Təsərrüfat vəziyyəti",
    "status_normal": "Normal",
    "status_attention": "Diqqət tələb edir",
    "weather": "🌤️ Hava proqnozu",
    "subsidy": "💰 Subsidiya yoxla",
    "irrigation": "💧 Suvarma vaxtı",
    "sima_auth": "✓ SİMA ilə doğrulanmışdır",
    "quick_actions": "Sürətli əməliyyatlar",
    # Settings strings
    "settings_language": "Dil / Language",
    "settings_notifications": "Bildirişlər",
    "settings_detail_level": "Cavab təfərrüatı",
    "settings_units": "Ölçü vahidləri",
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
    
    Args:
        user: Authenticated user (from OAuth) for loading persisted settings
    """
    # Load persisted settings if user is authenticated
    persisted = await load_user_settings(user)
    
    # Map persisted values to initial indices
    language_values = ["Azərbaycanca", "English", "Русский"]
    detail_values = ["Qısa", "Orta", "Ətraflı"]
    unit_values = ["Metrik (ha, kg)", "Yerli (sotka, pud)"]
    
    language_idx = language_values.index(persisted.get("language", "Azərbaycanca")) if persisted.get("language") in language_values else 0
    detail_idx = detail_values.index(persisted.get("detail_level", "Orta")) if persisted.get("detail_level") in detail_values else 1
    units_idx = unit_values.index(persisted.get("units", "Metrik (ha, kg)")) if persisted.get("units") in unit_values else 0
    
    settings = await cl.ChatSettings(
        [
            Select(
                id="language",
                label=AZ_STRINGS["settings_language"],
                values=language_values,
                initial_index=language_idx,
                description="Yonca cavablarının dili",
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
    return settings


@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle user settings changes.
    
    Called when user modifies any setting in the sidebar.
    Settings are automatically stored in cl.user_session["chat_settings"].
    
    If data persistence is enabled, settings are ALSO saved to database
    so they persist across sessions.
    """
    user: Optional[cl.User] = cl.user_session.get("user")
    
    logger.info(
        "settings_updated",
        session_id=cl.user_session.get("id"),
        user=user.identifier if user else "anonymous",
        settings=settings,
    )
    
    # Persist settings to database if user is authenticated
    if user:
        saved = await save_user_settings(user, settings)
        if saved:
            logger.info("settings_persisted", user=user.identifier)
    
    # Acknowledge the change to user
    language = settings.get("language", "Azərbaycanca")
    if language == "English":
        await cl.Message(content="✅ Settings updated. I'll respond in English now.").send()
    elif language == "Русский":
        await cl.Message(content="✅ Настройки обновлены. Теперь я буду отвечать на русском.").send()
    else:
        await cl.Message(content="✅ Parametrlər yeniləndi.").send()


# ============================================
# DASHBOARD WELCOME (Agricultural Command Center)
# ============================================
# BRANDING NOTE: Use "Yonca" or "Yonca AI" in user-facing content.
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
    
    # Build the dashboard message with Liquid Glass card styling
    # The CSS classes reference styles defined in custom.css
    dashboard_content = f"""
## 🌾 Yonca AI — Kənd Təsərrüfatı Köməkçisi

{greeting}

---

### 📊 {AZ_STRINGS["farm_status"]}

<div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: linear-gradient(135deg, rgba(45, 90, 39, 0.08) 0%, rgba(168, 230, 207, 0.15) 100%); border-radius: 12px; border-left: 4px solid #2D5A27; margin: 8px 0;">
    <span style="font-size: 1.5em;">✅</span>
    <div>
        <strong style="color: #2D5A27;">{AZ_STRINGS["status_normal"]}</strong>
        <div style="font-size: 0.85em; color: #666; margin-top: 2px;">Son yoxlama: Bu gün, 09:45</div>
    </div>
</div>

<div style="display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, rgba(45, 90, 39, 0.1) 0%, rgba(168, 230, 207, 0.2) 100%); border: 1px solid rgba(45, 90, 39, 0.2); border-radius: 999px; padding: 6px 14px; font-size: 0.85em; color: #2D5A27; font-weight: 500; margin-top: 8px;">
    <span style="color: #2D5A27;">✓</span> SİMA inteqrasiyası üçün hazırlanmışdır
</div>

---

Mən sizin virtual aqronomam. Əkin, suvarma, gübrələmə və digər kənd təsərrüfatı məsələlərində kömək edə bilərəm.

**{AZ_STRINGS["quick_actions"]}** — aşağıdakı düymələrdən birini seçin:
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
        author="Yonca AI",
        actions=actions,
    ).send()


@cl.action_callback("weather")
async def on_weather_action(action: cl.Action):
    """Handle weather quick action button click."""
    # Remove the action buttons after click
    await action.remove()
    
    # Simulate user asking about weather
    await cl.Message(
        content="Bu günkü hava proqnozu necədir?",
        author="user",
    ).send()
    
    # Trigger the agent to respond
    msg = cl.Message(content="Bu günkü hava proqnozu necədir?")
    await on_message(msg)


@cl.action_callback("subsidy")
async def on_subsidy_action(action: cl.Action):
    """Handle subsidy check quick action button click."""
    await action.remove()
    
    await cl.Message(
        content="Hansı subsidiyalardan yararlana bilərəm?",
        author="user",
    ).send()
    
    msg = cl.Message(content="Hansı subsidiyalardan yararlana bilərəm?")
    await on_message(msg)


@cl.action_callback("irrigation")
async def on_irrigation_action(action: cl.Action):
    """Handle irrigation time quick action button click."""
    await action.remove()
    
    await cl.Message(
        content="Bu gün sahəmi suvarmağı tövsiyə edirsiniz?",
        author="user",
    ).send()
    
    msg = cl.Message(content="Bu gün sahəmi suvarmağı tövsiyə edirsiniz?")
    await on_message(msg)

# ============================================
# SESSION MANAGEMENT
# ============================================
@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with farm context, user tracking, and dashboard welcome."""
    session_id = cl.user_session.get("id")
    
    # Get authenticated user (if OAuth enabled)
    # This is the REAL user (developer/tester), separate from farmer profile
    user: Optional[cl.User] = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    user_email = user.metadata.get("email") if user and user.metadata else None
    
    # Store user info for Langfuse tracking
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("user_email", user_email)
    
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
    
    # Create response message for streaming
    response_msg = cl.Message(content="", author="Yonca AI")
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
            langfuse_handler = create_langfuse_handler(
                session_id=thread_id,           # Groups all messages in conversation
                user_id=user_id,                # Attributes costs to user
                tags=["demo-ui", "development", "direct-mode"],
                metadata={
                    "farm_id": farm_id,
                    "user_email": user_email,
                    "source": "chainlit"
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
