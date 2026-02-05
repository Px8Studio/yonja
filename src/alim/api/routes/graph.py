# src/ALİM/api/routes/graph.py
"""LangGraph execution routes - async API for graph invocation.

These routes proxy to the LangGraph Dev Server using the official SDK.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langgraph_sdk import get_client
from pydantic import BaseModel, Field

from alim.api.dependencies.api_key import get_api_key
from alim.config import settings

router = APIRouter(dependencies=[Depends(get_api_key)])


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

    # P0: Include Langfuse tracing metadata for HTTP mode
    config = {
        "metadata": {
            # Core identifiers
            "model": settings.active_llm_model,
            "provider": settings.llm_provider.value,
            "user_id": request.user_id,
            "farm_id": request.farm_id,
            "source": "fastapi",
            # Langfuse tracing context
            "langfuse_session_id": thread_id,
            "langfuse_user_id": request.user_id,
            "langfuse_tags": ["api", "http_mode"],
        }
    }

    try:
        # 3. Invoke using stream(stream_mode="values") to get final state
        final_state = {}
        async for event in client.runs.stream(
            thread_id=thread_id,
            assistant_id=settings.langgraph_graph_id,
            input=serialized_state,
            config=config,
            stream_mode="values",
            if_not_exists="create",  # Auto-create thread if missing
        ):
            if event.get("event") == "values":
                final_state = event.get("data", {})

        # Extract response - priority order
        response_text = final_state.get("current_response")
        if not response_text:
            messages = final_state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                response_text = (
                    last_msg.get("content")
                    if isinstance(last_msg, dict)
                    else getattr(last_msg, "content", "")
                )

        return GraphInvokeResponse(
            response=response_text or "Bağışlayın, cavab hazırlana bilmədi.",
            thread_id=thread_id,
            model=settings.active_llm_model,
            metadata={
                "nodes_visited": final_state.get("nodes_visited", []),
                "intent": final_state.get("intent"),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")


@router.post("/graph/stream", tags=["Graph"])
async def stream_graph(request: GraphInvokeRequest):
    """Stream graph execution events in real-time."""
    client = _get_sdk_client()

    async def event_generator():
        nonlocal request
        thread_id = request.thread_id
        if not thread_id:
            thread = await client.threads.create()
            thread_id = thread["thread_id"]

        serialized_state = {
            "current_input": request.message,
            "user_id": request.user_id,
            "language": request.language,
        }

        try:
            async for event in client.runs.stream(
                thread_id=thread_id,
                assistant_id=settings.langgraph_graph_id,
                input=serialized_state,
                stream_mode=["messages", "updates"],
                if_not_exists="create",  # Auto-create thread if missing
            ):
                # Map LangGraph SDK events to Frontend SSE format
                if event["event"] == "messages/partial":
                    for chunk in event["data"]:
                        if chunk.get("role") == "assistant" and "content" in chunk:
                            yield f"event: token\ndata: {chunk['content']}\n\n"

                elif event["event"] == "updates":
                    for node_name, updates in event["data"].items():
                        yield f"event: node\ndata: {node_name}\n\n"

            yield "event: done\ndata: [DONE]\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

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
