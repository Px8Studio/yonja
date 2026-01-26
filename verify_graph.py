import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))


async def test_compile():
    print("Testing graph compilation...")
    try:
        # Mock Checkpointer?
        # Actually, let's try to compile without checkpointer first or with MemorySaver if needed.
        # But compile_agent_graph_async imports get_checkpointer_async which might need DB.
        # Let's import the sync version which usually doesn't need async setup,
        # OR just mock the dependencies.

        # However, the error was in `create_agent_graph` / `create_agent_graph_with_mcp`
        # specifically "add_node('end', END)".
        # So we just need to call create_agent_graph().

        from alim.agent.graph import create_agent_graph, create_agent_graph_with_mcp

        print("Creating standard graph...")
        graph = create_agent_graph()
        graph.compile()
        print("Standard graph compiled.")

        print("Creating MCP graph...")
        # create_agent_graph_with_mcp is async
        graph_mcp = await create_agent_graph_with_mcp()
        graph_mcp.compile()
        print("MCP graph compiled.")
        # Validate against flattened graph nodes (without HITL)
        expected_nodes = {
            "setup",
            "pii_masking",
            "supervisor",
            "context_loader",
            "agronomist",
            "weather",
            "nl_to_sql",
            "vision_to_action",
            "validator",
        }
        actual_nodes = set(graph_mcp.nodes.keys())

        # Note: END is not in nodes.keys() for StateGraph usually, but let's check subset
        if not expected_nodes.issubset(actual_nodes):
            print(f"Missing nodes! Expected at least: {expected_nodes}, Got: {actual_nodes}")
            return False

        print("Compilation success!", actual_nodes)
        return True
    except Exception as e:
        print(f"Compilation FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(test_compile())
    except Exception as e:
        print(f"Test runner failed: {e}")
