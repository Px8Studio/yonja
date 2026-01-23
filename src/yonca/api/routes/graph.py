# src/yonca/api/routes/graph.py
"""LangGraph execution routes - async API for graph invocation.

These routes proxy to the LangGraph Dev Server, decoupling the FastAPI layer
from in-process graph execution. Critical for:
- Multi-user concurrency (async/non-blocking)
- Horizontal scaling (stateless API workers)
- Production deployment (separate graph runtime)
"""
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from yonca.config import settings
from yonca.langgraph.client import LangGraphClient, LangGraphClientError

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
# Routes
# ============================================================


@router.post("/graph/invoke", response_model=GraphInvokeResponse, tags=["Graph"])
async def invoke_graph(request: GraphInvokeRequest):
    """Invoke the LangGraph agent synchronously.

    Returns the complete response after graph execution completes.
    For streaming responses, use `/graph/stream` instead.

    This is fully async/non-blocking - handles concurrent requests efficiently.
    """
    async with LangGraphClient(
        base_url=settings.langgraph_base_url,
        graph_id=settings.langgraph_graph_id,
    ) as client:
        # Build initial state from request
        from yonca.agent.state import create_initial_state, serialize_state_for_api

        initial_state = create_initial_state(
            thread_id=request.thread_id or "",  # Will be created if empty
            user_input=request.message,
            user_id=request.user_id,
            language=request.language,
            system_prompt_override=request.system_prompt_override,
            scenario_context=request.scenario_context,
        )

        # Serialize state for HTTP API (converts LangChain messages to plain dicts)
        serialized_state = serialize_state_for_api(initial_state)

        # Prepare config for LangGraph
        config = {
            "metadata": {
                "model": settings.active_llm_model,
                "provider": settings.llm_provider.value,
                "user_id": request.user_id,
                "farm_id": request.farm_id,
            }
        }

        try:
            # Async invocation - non-blocking for concurrent users
            result = await client.invoke(
                input_state=serialized_state,  # Use serialized state
                thread_id=request.thread_id,
                config=config,
            )

            # Extract response from final state
            response_text = result.get("current_response", "")
            if not response_text:
                # Fallback: check messages array
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict):
                        response_text = last_msg.get("content", "")

            return GraphInvokeResponse(
                response=response_text or "Cavab əldə edilmədi.",
                thread_id=result.get("thread_id", request.thread_id or "unknown"),
                model=settings.active_llm_model,
                metadata={
                    "provider": settings.llm_provider.value,
                    "user_id": request.user_id,
                    "farm_id": request.farm_id,
                },
            )

        except LangGraphClientError as e:
            raise HTTPException(status_code=502, detail=f"Graph execution failed: {e}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}") from e


@router.post("/graph/stream", tags=["Graph"])
async def stream_graph(request: GraphInvokeRequest):
    """Stream graph execution events in real-time.

    Returns Server-Sent Events (SSE) for progressive response display.
    Fully async - handles multiple concurrent streaming sessions.
    """

    async def event_generator():
        """Async generator for SSE streaming."""
        async with LangGraphClient(
            base_url=settings.langgraph_base_url,
            graph_id=settings.langgraph_graph_id,
        ) as client:
            # Build initial state
            from yonca.agent.state import create_initial_state, serialize_state_for_api

            initial_state = create_initial_state(
                thread_id=request.thread_id or "",  # Will be created if empty
                user_input=request.message,
                user_id=request.user_id,
                language=request.language,
                system_prompt_override=request.system_prompt_override,
                scenario_context=request.scenario_context,
            )

            # Serialize state for HTTP API (converts LangChain messages to plain dicts)
            serialized_state = serialize_state_for_api(initial_state)

            config = {
                "metadata": {
                    "model": settings.active_llm_model,
                    "provider": settings.llm_provider.value,
                    "user_id": request.user_id,
                    "farm_id": request.farm_id,
                }
            }

            try:
                # Async streaming - concurrent-safe
                async for event in client.stream(
                    input_state=serialized_state,  # Use serialized state
                    thread_id=request.thread_id,
                    config=config,
                ):
                    # Extract node name and response content
                    if isinstance(event, dict):
                        # Send node events
                        for node_name, node_output in event.items():
                            if node_name == "__start__":
                                continue

                            yield f"event: node\ndata: {node_name}\n\n"

                            # Stream response content if available
                            if isinstance(node_output, dict):
                                response = node_output.get("current_response", "")
                                if response:
                                    yield f"event: token\ndata: {response}\n\n"

                yield "event: done\ndata: [DONE]\n\n"

            except LangGraphClientError as e:
                yield f"event: error\ndata: Graph execution failed: {e}\n\n"
            except Exception as e:
                yield f"event: error\ndata: Unexpected error: {e}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/threads", response_model=ThreadResponse, tags=["Graph"])
async def create_thread(request: ThreadCreateRequest | None = None):
    """Create a new conversation thread.

    Async operation - returns immediately with thread_id.
    """
    metadata = request.metadata if request else {}

    async with LangGraphClient(
        base_url=settings.langgraph_base_url,
        graph_id=settings.langgraph_graph_id,
    ) as client:
        try:
            thread_id = await client.ensure_thread(thread_id=None, metadata=metadata)
            return ThreadResponse(thread_id=thread_id, metadata=metadata)
        except LangGraphClientError as e:
            raise HTTPException(status_code=502, detail=f"Thread creation failed: {e}") from e


@router.get("/threads/{thread_id}", response_model=ThreadResponse, tags=["Graph"])
async def get_thread(thread_id: str):
    """Get thread metadata.

    Async read operation.
    """
    # For now, return basic thread info
    # TODO: Implement actual thread state retrieval from checkpointer
    return ThreadResponse(thread_id=thread_id, metadata={})


@router.delete("/threads/{thread_id}", tags=["Graph"])
async def delete_thread(thread_id: str):
    """Delete a conversation thread.

    Async delete operation.
    """
    # TODO: Implement thread deletion via checkpointer
    return {"deleted": True, "thread_id": thread_id}


@router.get("/graph/health", response_model=GraphHealthResponse, tags=["Graph"])
async def graph_health():
    """Check LangGraph Dev Server health.

    Async health check - non-blocking.
    """
    async with LangGraphClient(
        base_url=settings.langgraph_base_url,
        graph_id=settings.langgraph_graph_id,
    ) as client:
        try:
            health = await client.health()
            return GraphHealthResponse(
                healthy=health.get("status") == "ok",
                dev_server_url=settings.langgraph_base_url,
                graph_id=settings.langgraph_graph_id,
                provider=settings.llm_provider.value,
                model=settings.active_llm_model,
            )
        except LangGraphClientError:
            return GraphHealthResponse(
                healthy=False,
                dev_server_url=settings.langgraph_base_url,
                graph_id=settings.langgraph_graph_id,
                provider=settings.llm_provider.value,
                model=settings.active_llm_model,
            )
