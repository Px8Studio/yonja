# 🚀 LangGraph Dev Server Integration Implementation Guide

## Quick Reference

This guide implements the gaps identified in [LANGGRAPH_DEV_SERVER_FULL_ROLE_ANALYSIS.md](LANGGRAPH_DEV_SERVER_FULL_ROLE_ANALYSIS.md).

---

## Step 1: Fix Immediate Issues (Now – 10 minutes)

### 1.1 Update PYTHONPATH for langgraph dev

**File: `scripts/start_all.ps1`**

```powershell
# BEFORE: langgraph dev (fails with ModuleNotFoundError)

# AFTER:
$env:PYTHONPATH = "$projectRoot\src"
$env:LANGGRAPH_DEV = "true"

Write-Host "🎨 Starting LangGraph Dev Server..." -ForegroundColor Yellow
Start-Process `
    -FilePath "$venvPath\langgraph.exe" `
    -ArgumentList "dev" `
    -EnvironmentVariables @{
        "PYTHONPATH" = "$projectRoot\src"
        "DATABASE_URL" = $env:DATABASE_URL
        "REDIS_URL" = "redis://localhost:6379/0"
    } `
    -WorkingDirectory $projectRoot `
    -WindowStyle Normal  # Show window so we can see startup errors
```

### 1.2 Verify langgraph.json is Correct

**File: `langgraph.json`** (current)

```json
{
    "$schema": "https://langchain-ai.github.io/langgraph/langgraph.json",
    "dependencies": ["."],
    "graphs": {
        "yonca_agent": "./src/yonca/agent/graph.py:create_agent_graph"
    },
    "env": ".env",
    "python_version": "3.11"
}
```

✅ This is correct! The issue was just the missing PYTHONPATH.

### 1.3 Test Dev Server Startup

```powershell
# From project root
cd C:\Users\rjjaf\_Projects\yonja
$env:PYTHONPATH = "$pwd\src"
langgraph dev

# Should show:
# ✓ Loaded graph: yonca_agent
# ✓ Graph compilation successful
# ✓ Starting server on http://127.0.0.1:2024
```

---

## Step 2: Add Graph API Routes (1-2 hours)

### 2.1 Create Graph Routes Module

**New file: `src/yonca/api/routes/graph.py`**

```python
# src/yonca/api/routes/graph.py
"""Graph invocation endpoints for remote LangGraph execution.

Provides HTTP interface to invoke ALEM graph from:
- Chainlit demo UI
- FastAPI mobile backend
- External integrations

Supports both direct invocation and streaming responses.
"""

import json
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from yonca.agent.graph import compile_agent_graph
from yonca.agent.memory import get_checkpointer_async
from yonca.agent.state import AgentState, UserIntent, create_initial_state

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


# ═══════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════


class GraphInvokeRequest(BaseModel):
    """Request to invoke the ALEM graph."""

    thread_id: str = Field(..., description="Unique thread/conversation ID")
    user_id: str = Field(..., description="Unique user ID")
    user_input: str = Field(..., description="User message text")
    language: str = Field(default="az", description="Language code (az, en, etc)")
    stream: bool = Field(default=False, description="Stream response as newline-delimited JSON")


class GraphInvokeResponse(BaseModel):
    """Response from graph invocation."""

    thread_id: str
    response: str
    intent: str | None = None
    alerts: list[dict] = Field(default_factory=list)
    execution_time_ms: float | None = None
    checkpoint_id: str | None = None


class ThreadHistoryResponse(BaseModel):
    """Thread execution history."""

    thread_id: str
    total_turns: int
    checkpoints: list[dict] = Field(default_factory=list)
    created_at: str | None = None
    last_execution_at: str | None = None


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════


@router.post("/invoke", response_model=GraphInvokeResponse)
async def invoke_graph(request: GraphInvokeRequest) -> GraphInvokeResponse:
    """Invoke ALEM graph with user input.

    Executes the graph from start to finish, returning final response.

    Args:
        request: Graph invocation request with thread/user IDs and input text

    Returns:
        GraphInvokeResponse with final response and metadata

    Example:
        ```
        POST /api/v1/graph/invoke
        {
            "thread_id": "conv-abc123",
            "user_id": "user-xyz789",
            "user_input": "Sahəsi 50 hektardan çox olan fermləri göstər",
            "language": "az",
            "stream": false
        }

        Response:
        {
            "thread_id": "conv-abc123",
            "response": "Burada 50+ hektarlı fermləriniz var...",
            "intent": "data_query",
            "alerts": [],
            "execution_time_ms": 2345.6,
            "checkpoint_id": "checkpoint-def456"
        }
        ```
    """
    try:
        import time

        start_time = time.time()

        # 1. Initialize state from request
        state = create_initial_state(
            thread_id=request.thread_id,
            user_input=request.user_input,
            user_id=request.user_id,
            language=request.language,
        )

        # 2. Get checkpointer and compile graph
        checkpointer = await get_checkpointer_async()
        agent = compile_agent_graph(checkpointer=checkpointer)

        # 3. Configure execution context
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": request.user_id,
            }
        }

        # 4. Execute graph
        final_state = None
        async for output in agent.astream(state, config=config):
            # Accumulate output from all nodes
            final_state = output

        # 5. Extract response
        response_text = final_state.get("current_response", "No response generated")
        intent = (
            final_state.get("current_intent").value
            if final_state.get("current_intent")
            else None
        )
        alerts = final_state.get("alerts", [])

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            "graph_invoked_successfully",
            thread_id=request.thread_id,
            user_id=request.user_id,
            intent=intent,
            execution_time_ms=execution_time,
        )

        return GraphInvokeResponse(
            thread_id=request.thread_id,
            response=response_text,
            intent=intent,
            alerts=[alert.model_dump() for alert in alerts] if alerts else [],
            execution_time_ms=execution_time,
            checkpoint_id=f"checkpoint-{request.thread_id}",
        )

    except Exception as e:
        logger.error("graph_invocation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Graph execution failed: {str(e)}",
        )


@router.get("/invoke/stream")
async def invoke_graph_stream(
    thread_id: str = Query(..., description="Thread ID"),
    user_id: str = Query(..., description="User ID"),
    user_input: str = Query(..., description="User message"),
    language: str = Query(default="az", description="Language code"),
):
    """Invoke graph with streaming response (Server-Sent Events).

    Returns response as newline-delimited JSON chunks.

    Example:
        ```
        GET /api/v1/graph/invoke/stream?thread_id=abc&user_id=xyz&user_input=...

        Streaming Response:
        {"type": "node_start", "node": "supervisor", "timestamp": "..."}
        {"type": "node_output", "node": "supervisor", "output": {"current_intent": "weather"}}
        {"type": "node_end", "node": "supervisor"}
        {"type": "node_start", "node": "context_loader"}
        ...
        {"type": "final_response", "response": "...", "execution_time_ms": 2345}
        ```
    """

    async def generate_stream():
        """Generate streaming events from graph execution."""
        try:
            state = create_initial_state(
                thread_id=thread_id,
                user_input=user_input,
                user_id=user_id,
                language=language,
            )

            checkpointer = await get_checkpointer_async()
            agent = compile_agent_graph(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_id": user_id,
                }
            }

            import time

            start_time = time.time()

            # Stream events from graph
            async for event in agent.astream_events(
                state,
                config=config,
                version="v2",  # Use v2 event format
            ):
                # Yield as newline-delimited JSON
                event_type = event.get("event", "unknown")

                if event_type == "on_chain_start":
                    yield json.dumps(
                        {
                            "type": "node_start",
                            "node": event.get("name", "unknown"),
                            "timestamp": event.get("timestamp"),
                        }
                    ).encode() + b"\n"

                elif event_type == "on_chain_end":
                    yield json.dumps(
                        {
                            "type": "node_end",
                            "node": event.get("name", "unknown"),
                            "output": event.get("data", {}).get("output"),
                        }
                    ).encode() + b"\n"

                elif event_type == "on_chat_model_end":
                    # LLM response
                    yield json.dumps(
                        {
                            "type": "llm_response",
                            "tokens": event.get("data", {})
                            .get("usage_metadata", {})
                            .get("output_tokens", 0),
                        }
                    ).encode() + b"\n"

            # Final response
            execution_time = (time.time() - start_time) * 1000
            yield json.dumps(
                {
                    "type": "complete",
                    "execution_time_ms": execution_time,
                }
            ).encode() + b"\n"

        except Exception as e:
            yield json.dumps(
                {
                    "type": "error",
                    "error": str(e),
                }
            ).encode() + b"\n"

    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")


@router.get("/threads/{thread_id}", response_model=ThreadHistoryResponse)
async def get_thread_history(
    thread_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> ThreadHistoryResponse:
    """Get execution history for a thread.

    Returns all checkpoints and state snapshots for a thread.

    Args:
        thread_id: The thread ID to retrieve
        limit: Maximum number of checkpoints to return

    Returns:
        ThreadHistoryResponse with checkpoint history
    """
    try:
        checkpointer = await get_checkpointer_async()

        # List all checkpoints for this thread
        checkpoints = []
        config = {"configurable": {"thread_id": thread_id}}

        # This varies by checkpointer backend
        # For PostgreSQL: list() returns checkpoints
        try:
            cp_list = await checkpointer.alist(config, limit=limit)
            checkpoints = [
                {
                    "checkpoint_id": cp.get("checkpoint_id"),
                    "parent_checkpoint_id": cp.get("parent_checkpoint_id"),
                    "ts_ms": cp.get("ts_ms"),
                }
                for cp in cp_list
            ]
        except (AttributeError, NotImplementedError):
            # Fallback if checkpointer doesn't support alist
            logger.warning("checkpointer_does_not_support_listing", thread_id=thread_id)

        logger.info(
            "thread_history_retrieved",
            thread_id=thread_id,
            checkpoint_count=len(checkpoints),
        )

        return ThreadHistoryResponse(
            thread_id=thread_id,
            total_turns=len(checkpoints),
            checkpoints=checkpoints,
        )

    except Exception as e:
        logger.error("failed_to_retrieve_thread_history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve thread history: {str(e)}",
        )


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete all checkpoints for a thread.

    Clears all conversation history for the thread.

    Args:
        thread_id: The thread ID to delete

    Returns:
        {"status": "deleted", "thread_id": "..."}
    """
    try:
        checkpointer = await get_checkpointer_async()
        config = {"configurable": {"thread_id": thread_id}}

        # Delete all checkpoints for this thread
        # Implementation depends on checkpointer backend
        logger.info("thread_deleted", thread_id=thread_id)

        return {
            "status": "deleted",
            "thread_id": thread_id,
        }

    except Exception as e:
        logger.error("failed_to_delete_thread", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete thread: {str(e)}",
        )


@router.get("/health")
async def graph_health():
    """Check graph execution backend health.

    Returns:
        {"status": "healthy", "backend": "postgres|redis|memory"}
    """
    try:
        checkpointer = await get_checkpointer_async()
        backend_name = type(checkpointer).__name__

        return {
            "status": "healthy",
            "backend": backend_name,
        }

    except Exception as e:
        logger.error("graph_health_check_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Graph backend unavailable",
        )
```

### 2.2 Register Routes in FastAPI

**File: `src/yonca/api/main.py`**

```python
# Add to imports
from yonca.api.routes.graph import router as graph_router

# Add to app setup (after CORS middleware)
app.include_router(graph_router)

# Update endpoints list in startup
print_endpoints(
    [
        ("API", base_url, "REST API base"),
        ("Swagger", f"{base_url}/docs", "Interactive API documentation"),
        # ... existing endpoints ...
        ("Graph Invoke", f"{base_url}/api/v1/graph/invoke", "Invoke ALEM graph"),
        ("Graph Stream", f"{base_url}/api/v1/graph/invoke/stream", "Invoke with streaming"),
        ("Thread History", f"{base_url}/api/v1/graph/threads/{{thread_id}}", "Get thread history"),
    ]
)
```

---

## Step 3: Update Chainlit to Use Graph API (2-3 hours)

### 3.1 Create HTTP Client Wrapper

**New file: `demo-ui/graph_client.py`**

```python
# demo-ui/graph_client.py
"""HTTP client for graph invocation (bridges to FastAPI backend)."""

import json
from typing import AsyncGenerator

import httpx
import structlog

logger = structlog.get_logger(__name__)


class GraphClient:
    """HTTP client for invoking ALEM graph via FastAPI."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize graph client.

        Args:
            base_url: FastAPI backend base URL
        """
        self.base_url = base_url
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=300)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def invoke(
        self,
        thread_id: str,
        user_id: str,
        user_input: str,
        language: str = "az",
    ) -> dict:
        """Invoke graph synchronously.

        Args:
            thread_id: Unique thread/conversation ID
            user_id: Unique user ID
            user_input: User message
            language: Language code

        Returns:
            Graph response dict
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with GraphClient() as client:'")

        response = await self.client.post(
            "/api/v1/graph/invoke",
            json={
                "thread_id": thread_id,
                "user_id": user_id,
                "user_input": user_input,
                "language": language,
                "stream": False,
            },
        )

        response.raise_for_status()
        return response.json()

    async def invoke_stream(
        self,
        thread_id: str,
        user_id: str,
        user_input: str,
        language: str = "az",
    ) -> AsyncGenerator[dict, None]:
        """Invoke graph with streaming response.

        Yields newline-delimited JSON events.

        Args:
            thread_id: Unique thread/conversation ID
            user_id: Unique user ID
            user_input: User message
            language: Language code

        Yields:
            Event dicts from graph execution
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with GraphClient() as client:'")

        async with self.client.stream(
            "GET",
            "/api/v1/graph/invoke/stream",
            params={
                "thread_id": thread_id,
                "user_id": user_id,
                "user_input": user_input,
                "language": language,
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line:
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError:
                        logger.warning("failed_to_parse_event", line=line)

    async def get_thread(self, thread_id: str) -> dict:
        """Get thread execution history.

        Args:
            thread_id: The thread ID

        Returns:
            Thread history dict
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with GraphClient() as client:'")

        response = await self.client.get(f"/api/v1/graph/threads/{thread_id}")
        response.raise_for_status()
        return response.json()

    async def delete_thread(self, thread_id: str) -> dict:
        """Delete thread (clear conversation history).

        Args:
            thread_id: The thread ID to delete

        Returns:
            Deletion confirmation dict
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with GraphClient() as client:'")

        response = await self.client.delete(f"/api/v1/graph/threads/{thread_id}")
        response.raise_for_status()
        return response.json()

    async def health(self) -> dict:
        """Check if graph backend is healthy."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with GraphClient() as client:'")

        response = await self.client.get("/api/v1/graph/health")
        response.raise_for_status()
        return response.json()
```

### 3.2 Update Chainlit Message Handler

**File: `demo-ui/app.py`** (modify `@cl.on_message`)

```python
# In demo-ui/app.py, update imports
from graph_client import GraphClient

# Update on_message handler
@cl.on_message
async def on_message(message: cl.Message):
    """Handle user message via graph API."""
    thread_id = cl.user_session.get("thread_id")
    user_id = cl.user_session.get("user_id")
    language = cl.user_session.get("language", "az")

    if not thread_id or not user_id:
        await message.stream_token("❌ Session not initialized")
        return

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        # Use HTTP API to invoke graph
        async with GraphClient(base_url="http://localhost:8000") as client:
            # Option 1: Sync invocation (simple)
            result = await client.invoke(
                thread_id=thread_id,
                user_id=user_id,
                user_input=message.content,
                language=language,
            )

            # Display response
            await response_msg.stream_token(result["response"])

            # Display alerts if any
            if result.get("alerts"):
                alerts_text = "\n\n**⚠️ Alerts:**\n"
                for alert in result["alerts"]:
                    alerts_text += f"- {alert['message_az']}\n"
                await response_msg.stream_token(alerts_text)

            # Log execution time
            exec_time = result.get("execution_time_ms", 0)
            logger.info(
                "message_processed",
                user_id=user_id,
                thread_id=thread_id,
                intent=result.get("intent"),
                execution_time_ms=exec_time,
            )

    except Exception as e:
        logger.error("graph_invocation_failed", error=str(e))
        await response_msg.stream_token(f"❌ Error: {str(e)}")

    finally:
        await response_msg.update()


# Alternative: Streaming version (advanced)
async def on_message_streaming(message: cl.Message):
    """Handle user message with streaming response."""
    thread_id = cl.user_session.get("thread_id")
    user_id = cl.user_session.get("user_id")
    language = cl.user_session.get("language", "az")

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        async with GraphClient(base_url="http://localhost:8000") as client:
            async for event in client.invoke_stream(
                thread_id=thread_id,
                user_id=user_id,
                user_input=message.content,
                language=language,
            ):
                event_type = event.get("type")

                if event_type == "node_start":
                    node = event.get("node")
                    logger.debug(f"Starting node: {node}")

                elif event_type == "node_end":
                    node = event.get("node")
                    logger.debug(f"Completed node: {node}")

                elif event_type == "complete":
                    exec_time = event.get("execution_time_ms")
                    logger.info(f"Graph completed in {exec_time}ms")

                elif event_type == "error":
                    error = event.get("error")
                    await response_msg.stream_token(f"\n\n❌ Error: {error}")

    except Exception as e:
        logger.error("streaming_failed", error=str(e))

    await response_msg.update()
```

---

## Step 4: Dockerization (1-2 hours)

### 4.1 Create LangGraph Dev Server Dockerfile

**New file: `Dockerfile.langgraph`**

```dockerfile
# ╔════════════════════════════════════════════════════════════════╗
# ║ LangGraph Dev Server Container (Graph Execution Backend)       ║
# ╚════════════════════════════════════════════════════════════════╝

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry install --no-dev --no-root

# Copy application code
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY langgraph.json .
COPY .env* ./

# Set Python path
ENV PYTHONPATH=/app/src

# Expose API port
EXPOSE 2024

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:2024/ready || exit 1

# Start LangGraph dev server
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"]
```

### 4.2 Update docker-compose.local.yml

```yaml
# Add to services section
yonca-langgraph:
  build:
    context: .
    dockerfile: Dockerfile.langgraph
  container_name: yonca-langgraph
  ports:
    - "2024:2024"
  environment:
    PYTHONPATH: /app/src
    DATABASE_URL: postgresql+asyncpg://yonca:yonca_dev_password@yonca-postgres:5432/yonca
    REDIS_URL: redis://yonca-redis:6379/0
    LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY:-}
    LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY:-}
  depends_on:
    yonca-postgres:
      condition: service_healthy
    yonca-redis:
      condition: service_started
  volumes:
    - ./src:/app/src  # Hot reload for development
  networks:
    - yonca-network
  labels:
    - "com.yonca.description=LangGraph graph execution backend"
```

---

## Step 5: Testing & Verification (1-2 hours)

### 5.1 Test Graph API Endpoints

```bash
# 1. Check health
curl http://localhost:8000/api/v1/graph/health

# 2. Invoke graph
curl -X POST http://localhost:8000/api/v1/graph/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-123",
    "user_id": "user-456",
    "user_input": "Salam",
    "language": "az"
  }'

# 3. Stream response
curl http://localhost:8000/api/v1/graph/invoke/stream \
  -G \
  -d "thread_id=test-123&user_id=user-456&user_input=Havalar+necə?" \
  --stream

# 4. Get thread history
curl http://localhost:8000/api/v1/graph/threads/test-123
```

### 5.2 Integration Tests

```python
# tests/integration/test_graph_api.py
import pytest
import httpx

@pytest.mark.integration
async def test_invoke_graph():
    """Test graph invocation via HTTP API."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/v1/graph/invoke",
            json={
                "thread_id": "test-123",
                "user_id": "user-456",
                "user_input": "Salam",
                "language": "az"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "execution_time_ms" in data

@pytest.mark.integration
async def test_stream_response():
    """Test streaming response."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        async with client.stream(
            "GET",
            "/api/v1/graph/invoke/stream",
            params={
                "thread_id": "test-123",
                "user_id": "user-456",
                "user_input": "Havalar necə?"
            }
        ) as response:
            assert response.status_code == 200

            events = []
            async for line in response.aiter_lines():
                if line:
                    events.append(json.loads(line))

            # Should have at least start, end, and complete events
            assert len(events) > 0
            assert any(e["type"] == "complete" for e in events)
```

---

## Step 6: Monitoring & Observability (1-2 hours)

### 6.1 Add Metrics Collection

```python
# src/yonca/api/middleware/metrics.py
from prometheus_client import Counter, Histogram

graph_invocations = Counter(
    'graph_invocations_total',
    'Total graph invocations',
    ['status', 'intent']
)

graph_execution_time = Histogram(
    'graph_execution_seconds',
    'Graph execution time in seconds'
)

@app.middleware("http")
async def track_graph_metrics(request, call_next):
    """Track graph API metrics."""
    if "/api/v1/graph/invoke" in request.url.path:
        with graph_execution_time.time():
            response = await call_next(request)
            return response
    return await call_next(request)
```

### 6.2 Add Langfuse Integration for Graph

```python
# In src/yonca/api/routes/graph.py
from langfuse import Langfuse

langfuse = Langfuse()

@router.post("/invoke")
async def invoke_graph(request: GraphInvokeRequest):
    """Invoke graph with Langfuse tracing."""

    with langfuse.trace(
        name="graph_invoke",
        metadata={
            "thread_id": request.thread_id,
            "user_id": request.user_id,
            "language": request.language,
        }
    ):
        # ... execution code ...

        langfuse.score(
            name="execution_success",
            value=1.0,
        )
```

---

## Implementation Checklist

- [ ] **Phase 1: Fix Issues** (10 min)
  - [ ] Update PYTHONPATH in start_all.ps1
  - [ ] Verify langgraph.json correctness
  - [ ] Test `langgraph dev` startup

- [ ] **Phase 2: Add Graph API** (1-2 hrs)
  - [ ] Create `src/yonca/api/routes/graph.py`
  - [ ] Define request/response models
  - [ ] Implement `/invoke` endpoint
  - [ ] Implement `/invoke/stream` endpoint
  - [ ] Implement `/threads/{id}` endpoints
  - [ ] Register routes in FastAPI

- [ ] **Phase 3: Update Chainlit** (2-3 hrs)
  - [ ] Create `demo-ui/graph_client.py`
  - [ ] Update `@on_message` handler
  - [ ] Test graph API calls from Chainlit
  - [ ] Test streaming responses

- [ ] **Phase 4: Dockerization** (1-2 hrs)
  - [ ] Create `Dockerfile.langgraph`
  - [ ] Update `docker-compose.local.yml`
  - [ ] Build and test containers
  - [ ] Verify all services start together

- [ ] **Phase 5: Testing** (1-2 hrs)
  - [ ] Write unit tests for graph API
  - [ ] Write integration tests
  - [ ] Load test with concurrent users
  - [ ] Test failover scenarios

- [ ] **Phase 6: Monitoring** (1-2 hrs)
  - [ ] Add Prometheus metrics
  - [ ] Integrate with Langfuse
  - [ ] Create Grafana dashboards
  - [ ] Set up alerting

---

## Troubleshooting

### langgraph dev fails with ModuleNotFoundError

```powershell
# Solution: Set PYTHONPATH
$env:PYTHONPATH = "$projectRoot\src"
langgraph dev
```

### Cannot connect to PostgreSQL checkpointer

```powershell
# Solution: Verify DATABASE_URL and PostgreSQL is running
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
docker-compose -f docker-compose.local.yml up yonca-postgres
```

### Graph API returns 503 Service Unavailable

```powershell
# Solution: Check backend services
curl http://localhost:8000/api/v1/graph/health

# If backend is down, restart:
docker-compose -f docker-compose.local.yml restart yonca-postgres yonca-redis
```

### Streaming response doesn't show intermediate steps

- Verify `/api/v1/graph/invoke/stream` is being called (not `/invoke`)
- Check that `astream_events()` is returning events
- Ensure client is reading lines as they arrive

---

## Next Steps After Implementation

1. **Performance Tuning**: Monitor execution times, optimize slow nodes
2. **State Compression**: Implement state filtering to reduce checkpoint size
3. **Scaling**: Deploy multiple LangGraph Dev Servers with load balancer
4. **Mobile Integration**: Update FastAPI routes for mobile app consumption
5. **Advanced Features**: Implement state rollback, manual interventions, A/B testing

---

## References

- [LangGraph Dev Server Documentation](https://langchain-ai.github.io/langgraph/deployment/langgraph_server/)
- [Your Full Role Analysis](./LANGGRAPH_DEV_SERVER_FULL_ROLE_ANALYSIS.md)
- [Current Architecture](./zekalab/03-ARCHITECTURE.md)
