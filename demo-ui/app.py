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
from chainlit.input_widget import Select
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
import structlog

# Import from main yonca package
from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer_async
from yonca.observability import create_langfuse_handler

# Import demo-ui config for Redis URL
from config import settings as demo_settings

logger = structlog.get_logger()

# Global checkpointer (initialized once in async context)
_checkpointer = None


async def get_app_checkpointer():
    """Get or create the checkpointer singleton (async)."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await get_checkpointer_async(redis_url=demo_settings.redis_url)
    return _checkpointer


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
}

# ============================================
# SESSION MANAGEMENT
# ============================================
@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with farm context and user tracking."""
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
    
    # Initialize the agent graph with shared checkpointer
    checkpointer = await get_app_checkpointer()
    agent = compile_agent_graph(checkpointer=checkpointer)
    cl.user_session.set("agent", agent)
    
    # Store thread_id for LangGraph (use session_id for continuity)
    cl.user_session.set("thread_id", session_id)
    
    logger.info(
        "session_started",
        session_id=session_id,
        user_id=user_id,
        user_email=user_email,
        farm_id=farm_id,
        oauth_enabled=is_oauth_enabled(),
    )
    
    # Personalized welcome for authenticated users
    if user and user.metadata:
        user_name = user.metadata.get("name", "").split()[0]  # First name
        welcome = f"🌾 **Salam, {user_name}!** Yonca AI Köməkçisinə xoş gəlmisiniz!\n\nMən sizin virtual aqronomam. Əkin, suvarma, gübrələmə və digər kənd təsərrüfatı məsələlərində kömək edə bilərəm."
    else:
        welcome = AZ_STRINGS["welcome"]
    
    # Send welcome message
    await cl.Message(
        content=welcome,
        author="Yonca"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages with Langfuse tracking."""
    session_id = cl.user_session.get("id")
    farm_id = cl.user_session.get("farm_id", "demo_farm_001")
    thread_id = cl.user_session.get("thread_id", session_id)
    agent = cl.user_session.get("agent")
    
    # Get real user identity (for Langfuse tracking)
    user_id = cl.user_session.get("user_id", "anonymous")
    user_email = cl.user_session.get("user_email")
    
    if not agent:
        # Re-initialize if agent is missing (shouldn't happen)
        checkpointer = await get_app_checkpointer()
        agent = compile_agent_graph(checkpointer=checkpointer)
        cl.user_session.set("agent", agent)
    
    # Create response message for streaming
    response_msg = cl.Message(content="", author="Yonca")
    await response_msg.send()
    
    # Build input for the agent
    input_messages = {
        "messages": [HumanMessage(content=message.content)]
    }
    
    # Create Langfuse handler for observability
    # This tracks: real user (developer) + synthetic farmer profile
    langfuse_handler = create_langfuse_handler(
        session_id=thread_id,
        user_id=user_id,  # Real user's email/identity
        tags=["demo-ui", "development"],
        metadata={
            "farm_id": farm_id,  # Synthetic farmer profile being tested
            "user_email": user_email,
            "source": "chainlit",
        },
        trace_name="demo_chat",
    )
    
    # Build callbacks list (type: ignore needed for mixed callback types)
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
    
    full_response = ""
    
    try:
        # Stream events from the agent
        async for event in agent.astream_events(input_messages, config=config, version="v2"):
            kind = event.get("event")
            
            # Handle different event types
            if kind == "on_chat_model_stream":
                # Token streaming from LLM
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    full_response += token
                    await response_msg.stream_token(token)
            
            elif kind == "on_chain_end":
                # Check for final output in chain end
                output = event.get("data", {}).get("output")
                if output and isinstance(output, dict):
                    messages = output.get("messages", [])
                    if messages and not full_response:
                        # Fallback: if streaming didn't work, get final message
                        last_msg = messages[-1]
                        if isinstance(last_msg, AIMessage) and last_msg.content:
                            full_response = last_msg.content
                            await response_msg.stream_token(full_response)
        
        # Finalize the message
        if not full_response:
            # Last resort: invoke synchronously to debug
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
