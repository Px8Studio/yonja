# src/ALİM/agent/nodes/nl_to_sql.py
"""NL-to-SQL node for converting farmer questions into SQL.

Uses the configured InferenceEngine and prompts the model to output
PostgreSQL-only SQL with no explanations. Assumes ALİM App DB has
tables like farms, parcels, crops, users. Validation ensures output
contains a SELECT statement.
"""


from typing import Annotated

import structlog
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from alim.agent.state import UserIntent, add_assistant_message
from alim.llm.inference_engine import InferenceEngine
from alim.llm.providers.base import LLMMessage

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = (
    "Sən verilənlər bazası sorğusu generatorusan. Verilən təsvirə uyğun olaraq "
    "yalnız SQL çıxışı ver. İzah yazma. Kod blokları (```sql) istifadə etmə. "
    "PostgreSQL dialektindən istifadə et. Cədvəl adları nümunə üçün: farms, parcels, crops, users. "
    "Tarixləri ISO formatında (YYYY-MM-DD) yaz. Lazım olduqda JOIN və WHERE istifadə et."
)


# ============================================================
# Node Schemas (State Isolation)
# ============================================================


class NLToSQLInput(TypedDict):
    """Input schema for NL-to-SQL node."""

    current_input: str
    nodes_visited: list[str]


class NLToSQLOutput(TypedDict):
    """Output schema for NL-to-SQL node."""

    current_response: str
    nodes_visited: list[str]
    messages: Annotated[list[BaseMessage], add_messages]
    error: str | None


# ============================================================
# NL-to-SQL Node
# ============================================================


async def nl_to_sql_node(state: NLToSQLInput) -> NLToSQLOutput:
    """Generate SQL from natural language input.

    Args:
        state: Current agent state
    Returns:
        State updates including current_response with SQL text
    """
    user_input = state.get("current_input", "")
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("nl_to_sql")

    logger.info(
        "nl_to_sql_node_start",
        message=user_input[:100],
    )

    engine = InferenceEngine()

    messages = [
        LLMMessage.system(SYSTEM_PROMPT),
        LLMMessage.user(user_input),
    ]

    try:
        resp = await engine.generate(messages, temperature=0.0, max_tokens=300)
        sql = resp.content.strip()
        # Minimal validation: must contain SELECT
        if "select" not in sql.lower():
            sql = "-- Generated SQL placeholder\nSELECT 1;"

        logger.info(
            "nl_to_sql_node_complete",
            sql_length=len(sql),
            has_select=bool("select" in sql.lower()),
        )

        return {
            "current_response": sql,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, sql, "nl_to_sql", UserIntent.DATA_QUERY)],
        }
    except Exception as e:
        logger.error(
            "nl_to_sql_node_error",
            error=str(e),
        )
        error_msg = "SQL generasiyası zamanı xəta baş verdi"
        return {
            "error": error_msg,
            "nodes_visited": nodes_visited,
            "messages": [
                add_assistant_message(state, error_msg, "nl_to_sql", UserIntent.DATA_QUERY)
            ],
        }
