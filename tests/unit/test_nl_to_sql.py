import asyncio
import types

import pytest

from yonca.agent.state import AgentState
from yonca.agent.nodes.nl_to_sql import nl_to_sql_node

class DummyResp:
    def __init__(self, content: str):
        self.content = content
        self.model = "dummy"
        self.tokens_used = 0
        self.finish_reason = "stop"
        self.metadata = {}

class DummyEngine:
    async def generate(self, messages, temperature=0.0, max_tokens=300):
        return DummyResp("SELECT * FROM farms;")

@pytest.mark.asyncio
async def test_nl_to_sql_node_generates_select(monkeypatch):
    # Patch InferenceEngine to our dummy
    import yonca.agent.nodes.nl_to_sql as mod
    mod.InferenceEngine = lambda: DummyEngine()

    state: AgentState = {
        "current_input": "Fermer təsvirinə görə təsərrüfatların siyahısını çıxart",
        "nodes_visited": [],
    }
    out = await nl_to_sql_node(state)
    assert "current_response" in out
    assert "SELECT" in out["current_response"].upper()
    assert "nodes_visited" in out and "nl_to_sql" in out["nodes_visited"]
