# src/ALİM/agent/nodes/sql_executor.py
"""Execute NL-generated SQL against ALİM App DB.

Takes SQL from nl_to_sql node output and safely executes it,
returning results as formatted markdown table for display to farmer.
"""

from typing import Any

import structlog

from alim.agent.state import AgentState, UserIntent, add_assistant_message
from alim.data.database import get_db_session

logger = structlog.get_logger(__name__)


async def sql_executor_node(state: AgentState) -> dict[str, Any]:
    """Execute SQL and format results.

    Assumes previous node (nl_to_sql) left SQL in current_response.
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("sql_executor")

    sql_text = state.get("current_response", "").strip()

    logger.info(
        "sql_executor_node_start",
        sql_length=len(sql_text),
        is_select=sql_text.upper().startswith("SELECT"),
    )

    if not sql_text or not sql_text.upper().startswith("SELECT"):
        return {
            "current_response": "SQL sorğusu tapmadı. Lütfen yenidən cəhd edin.",
            "nodes_visited": nodes_visited,
        }

    try:
        async with get_db_session() as session:
            result = await session.execute(sql_text)
            rows = result.fetchall()

        if not rows:
            formatted = "Nəticə: Heç bir rəkord tapılmadı."
        else:
            # Format as markdown table
            cols = [c for c in result.keys()] if result.keys() else ["col"]
            header = " | ".join(cols)
            sep = " | ".join(["---"] * len(cols))
            body_lines = [" | ".join(str(v) for v in row) for row in rows]
            formatted = f"| {header} |\n| {sep} |\n" + "\n".join(
                f"| {line} |" for line in body_lines
            )

        logger.info(
            "sql_executor_node_complete",
            rows_returned=len(rows),
        )

        return {
            "current_response": formatted,
            "nodes_visited": nodes_visited,
            "messages": [
                add_assistant_message(state, formatted, "sql_executor", UserIntent.DATA_QUERY)
            ],
        }
    except Exception as e:
        logger.error(
            "sql_executor_node_error",
            error=str(e)[:100],
        )
        error_msg = f"SQL xətası: {str(e)[:100]}"
        return {
            "error": error_msg,
            "current_response": error_msg,
            "nodes_visited": nodes_visited,
        }
