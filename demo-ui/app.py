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

# Fix engineio packet limit before chainlit imports
import engineio
engineio.payload.Payload.max_decode_packets = 500

import chainlit as cl
from chainlit.input_widget import Select
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
import structlog

# Import from main yonca package
from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer

logger = structlog.get_logger()

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
    """Initialize chat session with farm context."""
    session_id = cl.user_session.get("id")
    
    # Default farm for demo
    farm_id = "demo_farm_001"
    cl.user_session.set("farm_id", farm_id)
    
    # Initialize the agent graph with checkpointer
    checkpointer = get_checkpointer()
    agent = compile_agent_graph(checkpointer=checkpointer)
    cl.user_session.set("agent", agent)
    
    # Store thread_id for LangGraph (use session_id for continuity)
    cl.user_session.set("thread_id", session_id)
    
    logger.info("session_started", session_id=session_id, farm_id=farm_id)
    
    # Send welcome message
    await cl.Message(
        content=AZ_STRINGS["welcome"],
        author="Yonca"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    session_id = cl.user_session.get("id")
    farm_id = cl.user_session.get("farm_id", "demo_farm_001")
    thread_id = cl.user_session.get("thread_id", session_id)
    agent = cl.user_session.get("agent")
    
    if not agent:
        # Re-initialize if agent is missing (shouldn't happen)
        checkpointer = get_checkpointer()
        agent = compile_agent_graph(checkpointer=checkpointer)
        cl.user_session.set("agent", agent)
    
    # Create response message for streaming
    response_msg = cl.Message(content="", author="Yonca")
    await response_msg.send()
    
    # Build input for the agent
    input_messages = {
        "messages": [HumanMessage(content=message.content)]
    }
    
    # LangGraph config with thread_id for memory
    config = RunnableConfig(
        configurable={
            "thread_id": thread_id,
            "farm_id": farm_id,
        },
        callbacks=[cl.LangchainCallbackHandler()],
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
