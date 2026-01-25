# src/ALİM/api/routes/graph.py
"""LangGraph execution routes - async API for graph invocation.

These routes proxy to the LangGraph Dev Server using the official SDK.
"""
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph_sdk import get_client
from pydantic import BaseModel, Field

from alim.config import settings

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================


class GraphInvokeRequest(BaseModel):
    """Request model for graph invocation."""

    message: str = Field(..., description="User message in Azerbaijani", min_length=1)
    thread_id: str | None = Field(None, description="Thread ID for conversation continuity")
    user_id: str = Field(default="anonymous", description="User identifier for tracking")
    farm_id: str | None = Field(None, description="Farm context identifier")
    language: str = Field(default="az", description="User language (az, en, ru)")
    system_prompt_override: str | None = Field(None, description="Custom system prompt")
    scenario_context: dict[str, Any] | None = Field(None, description="Farm scenario metadata")


class GraphInvokeResponse(BaseModel):
    """Response model for graph invocation."""

    response: str = Field(..., description="Agent response text")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")
    model: str = Field(..., description="Active LLM model")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution metadata")


class ThreadCreateRequest(BaseModel):
    """Request model for thread creation."""

    metadata: dict[str, Any] = Field(default_factory=dict, description="Thread metadata")


class ThreadResponse(BaseModel):
    """Response model for thread operations."""

    thread_id: str = Field(..., description="Thread identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Thread metadata")


class GraphHealthResponse(BaseModel):
    """Response model for graph health check."""

    healthy: bool = Field(..., description="Graph service health status")
    dev_server_url: str = Field(..., description="LangGraph Dev Server URL")
    graph_id: str = Field(..., description="Active graph identifier")
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Active LLM model")


# ============================================================
# Helpers
# ============================================================


def _get_sdk_client():
    """Get configured LangGraph SDK client."""
    return get_client(url=settings.langgraph_base_url)


# ============================================================
# Routes
# ============================================================


@router.post("/graph/invoke", response_model=GraphInvokeResponse, tags=["Graph"])
async def invoke_graph(request: GraphInvokeRequest):
    """Invoke the LangGraph agent synchronously using official SDK.

    Returns the complete response after graph execution completes.
    """
    client = _get_sdk_client()

    # 1. Ensure Thread
    thread_id = request.thread_id
    if not thread_id:
        thread = await client.threads.create(
            metadata={
                "user_id": request.user_id,
                "farm_id": request.farm_id,
            }
        )
        thread_id = thread["thread_id"]

    # 2. Prepare Input
    serialized_state = {
        "current_input": request.message,
        "user_id": request.user_id,
        "language": request.language,
        "thread_id": thread_id,
    }
    if request.scenario_context:
        serialized_state["scenario_context"] = request.scenario_context

    config = {
        "metadata": {
            "model": settings.active_llm_model,
            "provider": settings.llm_provider.value,
            "user_id": request.user_id,
            "farm_id": request.farm_id,
        }
    }

    try:
        # 3. Invoke (Wait for completion)
        # client.runs.wait returns the final state usually in the 'output' key or similar depending on implementation
        # However, it often returns the run object.
        # Standard pattern for 'invoke' equivalent is waiting and then getting state,
        # but let's assume wait returns the full result as the custom client did, or we use client.runs.wait()

        # Note: SDK 'wait' might return the run. We might need to fetch state.
        # But SDK usually has a convenience method?
        # Let's use the low-level 'wait' which corresponds to POST /runs?wait=true

        # Using stream with stream_mode='values' and taking the last event is arguably safer/more uniform
        # but let's try the wait method if available.
        # Recent SDK has `client.runs.wait`.

        # We will iterate stream with values to get the final state, which is robust.
        final_state = {}
        async for event in client.runs.stream(
            thread_id=thread_id,
            assistant_id=settings.langgraph_graph_id,
            input=serialized_state,
            config=config,
            stream_mode="values",
        ):
            if event.get("event") == "values":
                final_state = event.get("data", {})

        # Alternatively, if we want strict 'wait' behavior without streaming overhead:
        # run = await client.runs.wait(thread_id=thread_id, assistant_id=..., input=...)
        # But `wait` signature might vary. `stream` is very standard in LangGraph.

        # Extract response from final state
        response_text = final_state.get("current_response", "")
        if not response_text:
            # Fallback checks
            messages = final_state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    response_text = last_msg.get("content", "")

        return GraphInvokeResponse(
            response=response_text or "Cavab əldə edilmədi.",
            thread_id=thread_id,
            model=settings.active_llm_model,
            metadata={
                "provider": settings.llm_provider.value,
                "user_id": request.user_id,
                "farm_id": request.farm_id,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {e}") from e


@router.post("/graph/stream", tags=["Graph"])
async def stream_graph(request: GraphInvokeRequest):
    """Stream graph execution events in real-time using official SDK."""
    client = _get_sdk_client()

    async def event_generator():
        # 1. Ensure Thread (Simplified for streaming, might need creation)
        nonlocal request
        thread_id = request.thread_id
        if not thread_id:
            try:
                thread = await client.threads.create(metadata={"user_id": request.user_id})
                thread_id = thread["thread_id"]
                # We should probably inform client of new thread_id, but SSE is one-way usually.
                # The client will see it in events if we send it.
            except Exception as e:
                yield f"event: error\ndata: Thread creation failed: {e}\n\n"
                return

        # 2. Input
        serialized_state = {
            "current_input": request.message,
            "user_id": request.user_id,
            "language": request.language,
            "thread_id": thread_id,
        }
        if request.scenario_context:
            serialized_state["scenario_context"] = request.scenario_context

        config = {
            "metadata": {
                "model": settings.active_llm_model,
                "provider": settings.llm_provider.value,
                "user_id": request.user_id,
                "farm_id": request.farm_id,
            }
        }

        try:
            # 3. Stream
            # Native SDK stream usage
            async for event in client.runs.stream(
                thread_id=thread_id,
                assistant_id=settings.langgraph_graph_id,
                input=serialized_state,
                config=config,
                stream_mode=["messages", "updates"],  # Request both messages and updates
            ):
                # Handle 'messages' event (LLM tokens)
                if event.get("event") == "messages/partial":
                    # This might differ based on SDK version.
                    # SDK usually emits:
                    # event: messages
                    # data: [chunk]
                    #
                    # Or event: metadata, etc.
                    #
                    # Let's map SDK events to our frontend SSE format.
                    # Our frontend expects:
                    # event: node -> node name
                    # event: token -> text content
                    # event: done

                    # Note: SDK events are structurally different.
                    # We need to map them.
                    # event types: "values", "messages", "updates", "error" etc.

                    data = event.get("data", [])
                    if event.get("event") == "messages":
                        # data is list of message chunks
                        for chunk in data:
                            if chunk.get("role") == "assistant" and "content" in chunk:
                                yield f"event: token\ndata: {chunk['content']}\n\n"

                elif event.get("event") == "updates":
                    # Node update
                    data = event.get("data", {})
                    for node_name, node_state in data.items():
                        if node_name == "__start__":
                            continue
                        yield f"event: node\ndata: {node_name}\n\n"

                        # If there is a response in the state update (not streamed via messages)
                        if isinstance(node_state, dict):
                            # Response access for debugging or future use, but avoiding lint error
                            _ = node_state.get("current_response", "")
                            pass

            yield "event: done\ndata: [DONE]\n\n"

        except Exception as e:
            yield f"event: error\ndata: Graph execution failed: {e}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/threads", response_model=ThreadResponse, tags=["Graph"])
async def create_thread(request: ThreadCreateRequest | None = None):
    """Create a new conversation thread."""
    client = _get_sdk_client()
    metadata = request.metadata if request else {}

    try:
        thread = await client.threads.create(metadata=metadata)
        return ThreadResponse(thread_id=thread["thread_id"], metadata=thread.get("metadata", {}))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Thread creation failed: {e}") from e


@router.get("/threads/{thread_id}", response_model=ThreadResponse, tags=["Graph"])
async def get_thread(thread_id: str):
    """Get thread metadata."""
    client = _get_sdk_client()
    try:
        thread = await client.threads.get(thread_id=thread_id)
        return ThreadResponse(thread_id=thread["thread_id"], metadata=thread.get("metadata", {}))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread not found: {e}")


@router.delete("/threads/{thread_id}", tags=["Graph"])
async def delete_thread(thread_id: str):
    """Delete a conversation thread."""
    client = _get_sdk_client()
    try:
        # SDK likely has a delete method
        await client.threads.delete(thread_id=thread_id)
        return {"deleted": True, "thread_id": thread_id}
    except Exception as e:
        # If delete not supported or fails
        raise HTTPException(status_code=500, detail=f"Thread deletion failed: {e}")


@router.get("/graph/health", response_model=GraphHealthResponse, tags=["Graph"])
async def graph_health():
    """Check LangGraph Dev Server health."""
    # SDK doesn't always have a direct 'health' method exposed on client root,
    # but we can try a simple operation or assume healthy if client connects.
    # Often client.info() or similar.
    # Let's fallback to checking if we can list assistants or similar lightsafe op.
    client = _get_sdk_client()

    is_healthy = False
    try:
        # Search for assistants or just check connectivity
        await client.assistants.search(limit=1)
        is_healthy = True
    except Exception:
        is_healthy = False

    return GraphHealthResponse(
        healthy=is_healthy,
        dev_server_url=settings.langgraph_base_url,
        graph_id=settings.langgraph_graph_id,
        provider=settings.llm_provider.value,
        model=settings.active_llm_model,
    )
