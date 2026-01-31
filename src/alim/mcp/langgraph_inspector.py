from typing import Any

from fastmcp import FastMCP
from langgraph_sdk import get_client

from alim.config import settings

# Initialize FastMCP
mcp = FastMCP("LangGraph Inspector")


def _get_client():
    """Get configured LangGraph SDK client."""
    return get_client(url=settings.langgraph_base_url)


@mcp.tool()
async def list_assistants() -> list[dict[str, Any]]:
    """List available graph assistants in the LangGraph server."""
    client = _get_client()
    assistants = await client.assistants.search()
    return assistants


@mcp.tool()
async def get_thread(thread_id: str) -> dict[str, Any]:
    """Get the state and metadata of a specific thread."""
    client = _get_client()
    try:
        thread = await client.threads.get(thread_id=thread_id)
        # Fetch current state as well which is often useful
        state = await client.threads.get_state(thread_id=thread_id)
        return {"metadata": thread, "state": state}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_threads(limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
    """Search for recent threads to find context."""
    client = _get_client()
    threads = await client.threads.search(limit=limit, offset=offset)
    return threads


@mcp.tool()
async def get_latest_run(thread_id: str) -> dict[str, Any]:
    """Get the most recent run for a specific thread."""
    client = _get_client()
    runs = await client.runs.list(thread_id=thread_id, limit=1)
    if runs:
        return runs[0]
    return {"message": "No runs found for this thread."}


if __name__ == "__main__":
    mcp.run()
