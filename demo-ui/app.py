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
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import chainlit as cl
from chainlit.input_widget import Select
from langchain_core.runnables import RunnableConfig
import structlog

# Import from main yonca package
from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer
from yonca.agent.state import create_initial_state

# Import demo services
from services.mock_data import MockDataService
from components.farm_selector import format_farm_context_for_prompt

logger = structlog.get_logger(__name__)

# ============================================
# LOCALIZATION (Azerbaijani)
# ============================================
AZ = {
    "welcome_title": "🌾 **Yonca AI Köməkçisinə xoş gəlmisiniz!**",
    "welcome_body": "Mən sizin virtual aqronomam. Əkin, suvarma, gübrələmə və digər kənd təsərrüfatı məsələlərində kömək edə bilərəm.",
    "farm_loaded": "📍 **Təsərrüfat yükləndi:** {farm_name}",
    "farm_changed": "📍 **Təsərrüfat dəyişdirildi:** {farm_name}",
    "farm_select_label": "Təsərrüfat seçin",
    "thinking": "Düşünürəm...",
    "error": "⚠️ Bağışlayın, texniki xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.",
    "feedback_thanks": "Rəyiniz üçün təşəkkür edirik! 🙏",
    # Node step names
    "step_supervisor": "🎯 Sorğu yönləndirilir",
    "step_context": "📂 Kontekst yüklənir",
    "step_agronomist": "🌱 Aqronomiya analizi",
    "step_weather": "🌤️ Hava məlumatları",
    "step_validator": "✅ Cavab yoxlanılır",
}


# ============================================
# LANGGRAPH SETUP
# ============================================

def get_compiled_graph():
    """Get or create the compiled LangGraph with checkpointer.
    
    Uses Redis checkpointer for session persistence.
    """
    try:
        checkpointer = get_checkpointer()
        return compile_agent_graph(checkpointer)
    except Exception:  # noqa: BLE001
        logger.warning("Could not connect to Redis, running without checkpointer")
        return compile_agent_graph(None)


# Module-level graph instance (lazy initialized)
_GRAPH = None


def get_graph():
    """Lazy initialization of the graph."""
    global _GRAPH  # noqa: PLW0603
    if _GRAPH is None:
        _GRAPH = get_compiled_graph()
    return _GRAPH


# ============================================
# SESSION START
# ============================================

@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session."""
    
    # Load demo farm data
    mock_service = MockDataService()
    farms = mock_service.get_all_farms()
    default_farm = farms[0] if farms else None
    
    # Store farm context in session
    cl.user_session.set("farm_context", default_farm)
    cl.user_session.set("all_farms", farms)
    
    # Create farm selector settings
    farm_options = mock_service.get_farm_selector_options()
    await cl.ChatSettings(
        [
            Select(
                id="farm_id",
                label=AZ["farm_select_label"],
                values=[opt["value"] for opt in farm_options],
                initial_value=farm_options[0]["value"] if farm_options else None,
            ),
        ]
    ).send()
    
    # Send welcome message
    welcome_msg = f"{AZ['welcome_title']}\n\n{AZ['welcome_body']}"
    await cl.Message(content=welcome_msg, author="Yonca").send()
    
    # Show selected farm info
    if default_farm:
        farm_info = _format_farm_info(default_farm)
        await cl.Message(
            content=AZ["farm_loaded"].format(farm_name=default_farm["name"]) + "\n\n" + farm_info,
            author="Sistem",
        ).send()
    
    logger.info(
        "session_started",
        session_id=cl.context.session.id,
        farm_id=default_farm["id"] if default_farm else None,
    )


def _format_farm_info(farm: dict) -> str:
    """Format farm information for display."""
    ndvi_display = f"{farm['last_ndvi']:.2f}" if farm.get("last_ndvi") else "N/A"
    return f"""
🌱 **Əkin:** {farm["crop"]}
📐 **Sahə:** {farm["area_ha"]} hektar  
🏔️ **Rayon:** {farm["district"]}, {farm["region"]}
🌍 **Torpaq:** {farm["soil_type"]}
💧 **Suvarma:** {farm["irrigation_type"]}
📊 **NDVI:** {ndvi_display}
"""


# ============================================
# SETTINGS CHANGE (Farm Selector)
# ============================================

@cl.on_settings_update
async def on_settings_update(settings: dict):
    """Handle farm selection change."""
    farm_id = settings.get("farm_id")
    if not farm_id:
        return
    
    farms = cl.user_session.get("all_farms", [])
    selected_farm = next((f for f in farms if f["id"] == farm_id), None)
    
    if selected_farm:
        # Update session
        cl.user_session.set("farm_context", selected_farm)
        
        # Notify user
        farm_info = _format_farm_info(selected_farm)
        await cl.Message(
            content=AZ["farm_changed"].format(farm_name=selected_farm["name"]) + "\n\n" + farm_info,
            author="Sistem",
        ).send()
        
        logger.info(
            "farm_changed",
            session_id=cl.context.session.id,
            farm_id=farm_id,
        )


# ============================================
# MESSAGE HANDLER (LangGraph Integration)
# ============================================

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages using LangGraph.
    
    Uses Chainlit's native LangchainCallbackHandler for automatic
    step visualization and streaming.
    """
    farm_context = cl.user_session.get("farm_context", {})
    
    # Create callback handler for step visualization
    # This automatically shows which LangGraph node is executing
    cb = cl.LangchainCallbackHandler(
        # Customize step names in Azerbaijani
        # to_keep=["supervisor", "context_loader", "agronomist", "weather", "validator"],
    )
    
    # Configure graph execution with session thread_id
    config = RunnableConfig(
        callbacks=[cb],
        configurable={
            # Use Chainlit session ID as thread_id for persistence
            "thread_id": cl.context.session.id,
        },
    )
    
    # Create initial state
    initial_state = create_initial_state(
        thread_id=cl.context.session.id,
        user_input=message.content,
        language="az",
    )
    
    # Add farm context to state for personalized responses
    if farm_context:
        initial_state["farm_context"] = farm_context
        # Include formatted context in the prompt
        initial_state["context"] = format_farm_context_for_prompt(farm_context)
    
    # Create response message placeholder
    response_msg = cl.Message(content="", author="Yonca")
    await response_msg.send()
    
    try:
        graph = get_graph()
        final_response = ""
        
        # Stream the response
        async for event in graph.astream(initial_state, config):
            # The callback handler (cb) automatically updates the UI
            # showing which node is executing
            
            # Extract the final response content
            if isinstance(event, dict):
                # Check for response in different possible locations
                if "response" in event:
                    final_response = event["response"]
                elif "messages" in event:
                    messages = event["messages"]
                    if messages and hasattr(messages[-1], "content"):
                        final_response = messages[-1].content
        
        # Update the response message with final content
        if final_response:
            response_msg.content = final_response
            await response_msg.update()
        else:
            # Fallback if no response was captured
            response_msg.content = "Bağışlayın, cavab hazırlana bilmədi. Zəhmət olmasa yenidən cəhd edin."
            await response_msg.update()
        
        logger.info(
            "message_handled",
            session_id=cl.context.session.id,
            user_message_length=len(message.content),
            response_length=len(final_response),
        )
        
    except Exception:  # noqa: BLE001
        logger.exception(
            "message_handler_error",
            session_id=cl.context.session.id,
        )
        response_msg.content = AZ["error"]
        await response_msg.update()


# ============================================
# SESSION END
# ============================================

@cl.on_chat_end
async def on_chat_end():
    """Clean up when session ends."""
    logger.info(
        "session_ended",
        session_id=cl.context.session.id,
    )


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # This allows running with: python app.py
    # But chainlit run app.py is preferred
    import chainlit.cli
    chainlit.cli.run_chainlit(__file__)
