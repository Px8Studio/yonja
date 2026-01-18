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

# Add project root to path for imports
project_root = Path(__file__).parent.parent
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

# Import demo-ui config and API client
from config import settings as demo_settings
from services.yonca_client import YoncaClient, YoncaClientError

logger = structlog.get_logger()

# Log integration mode at startup
logger.info(
    "demo_ui_starting",
    integration_mode=demo_settings.integration_mode,
    api_url=demo_settings.yonca_api_url if demo_settings.use_api_bridge else "N/A (direct)",
)

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
# Use @cl.on_settings_update to react to changes.
# ============================================
async def setup_chat_settings():
    """Initialize chat settings panel for user preferences.
    
    These settings appear in Chainlit's sidebar when the user clicks
    the settings icon. Values are stored in cl.user_session["chat_settings"].
    """
    settings = await cl.ChatSettings(
        [
            Select(
                id="language",
                label=AZ_STRINGS["settings_language"],
                values=["Azərbaycanca", "English", "Русский"],
                initial_index=0,
                description="Yonca cavablarının dili",
            ),
            Select(
                id="detail_level",
                label=AZ_STRINGS["settings_detail_level"],
                values=["Qısa", "Orta", "Ətraflı"],
                initial_index=1,
                description="Cavabların nə qədər ətraflı olacağı",
            ),
            Select(
                id="units",
                label=AZ_STRINGS["settings_units"],
                values=["Metrik (ha, kg)", "Yerli (sotka, pud)"],
                initial_index=0,
                description="Sahə və çəki ölçü vahidləri",
            ),
            Switch(
                id="notifications",
                label=AZ_STRINGS["settings_notifications"],
                initial=True,
                description="Suvarma və hava xəbərdarlıqları",
            ),
            Switch(
                id="show_sources",
                label="Mənbələri göstər",
                initial=False,
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
    """
    logger.info(
        "settings_updated",
        session_id=cl.user_session.get("id"),
        settings=settings,
    )
    
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
        author="Yonca",
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
    # This is the native Chainlit way to handle per-user preferences
    user_settings = await setup_chat_settings()
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
    response_msg = cl.Message(content="", author="Yonca")
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
                session_id=thread_id,
                user_id=user_id,
                tags=["demo-ui", "development", "direct-mode"],
                metadata={
                    "farm_id": farm_id,
                    "user_email": user_email,
                    "source": "chainlit",
                },
                trace_name="demo_chat",
            )
            
            # Build callbacks list
            callbacks: list = [cl.LangchainCallbackHandler()]  # type: ignore[type-arg]
            if langfuse_handler:
                callbacks.append(langfuse_handler)
            
            # LangGraph config with thread_id for memory
            config = RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "farm_id": farm_id,
                },
                callbacks=callbacks,  # type: ignore[arg-type]
            )
            
            # Stream events from the agent
            async for event in agent.astream_events(input_messages, config=config, version="v2"):
                kind = event.get("event")
                
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        token = chunk.content
                        full_response += token
                        await response_msg.stream_token(token)
                
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if output and isinstance(output, dict):
                        messages = output.get("messages", [])
                        if messages and not full_response:
                            last_msg = messages[-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                full_response = last_msg.content
                                await response_msg.stream_token(full_response)
            
            # Fallback if streaming didn't produce output
            if not full_response:
                logger.warning("no_streaming_response", session_id=session_id)
                result = await agent.ainvoke(input_messages, config=config)
                if result and "messages" in result:
                    for msg in reversed(result["messages"]):
                        if isinstance(msg, AIMessage) and msg.content:
                            full_response = msg.content
                            response_msg.content = full_response
                            await response_msg.update()
                            break
        
        # Update final content
        response_msg.content = full_response
        await response_msg.update()
        
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
