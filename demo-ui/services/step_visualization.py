# demo-ui/services/step_visualization.py
"""Chainlit Step API integration for agent visualization.

Provides decorators and utilities for showing LangGraph node execution
as visual progress steps in the Chainlit UI.
"""

import functools
from collections.abc import Callable
from typing import Any

import chainlit as cl
import structlog

logger = structlog.get_logger(__name__)

# Node name → Human-readable step labels (Azerbaijani)
NODE_STEP_LABELS = {
    "supervisor": "🧭 İstifadəçi niyyətinin təhlili",
    "context_loader": "📦 Kontekst məlumatlarının yüklənməsi",
    "agronomist": "🌾 Aqronom məsləhətinin hazırlanması",
    "weather": "🌤️ Hava proqnozunun yoxlanılması",
    "nl_to_sql": "🔍 Verilənlər bazası sorğusunun hazırlanması",
    "sql_executor": "⚡ Sorğunun icra edilməsi",
    "vision_to_action": "👁️ Şəklin təhlili",
    "validator": "✅ Cavabın yoxlanılması",
}

# Node name → Detailed descriptions
NODE_STEP_DESCRIPTIONS = {
    "supervisor": "İstifadəçinin sualını təsnif edir və uyğun eksperti seçir",
    "context_loader": "Fermer profili, təsərrüfat və hava məlumatlarını yükləyir",
    "agronomist": "Aqronomiya üzrə peşəkar məsləhət tərtib edir",
    "weather": "Cari və gələcək hava şəraitini təhlil edir",
    "nl_to_sql": "Təbii dildən SQL sorğusuna çevirir",
    "sql_executor": "Verilənlər bazasından məlumat əldə edir",
    "vision_to_action": "Yüklənmiş şəkli təhlil edir və tövsiyələr verir",
    "validator": "Cavabın keyfiyyətini və dəqiqliyini yoxlayır",
}


def get_step_label(node_name: str) -> str:
    """Get human-readable label for a LangGraph node.

    Args:
        node_name: Internal node name (e.g., "supervisor")

    Returns:
        Formatted label with emoji (e.g., "🧭 İstifadəçi niyyətinin təhlili")
    """
    return NODE_STEP_LABELS.get(node_name, f"⚙️ {node_name}")


def get_step_description(node_name: str) -> str:
    """Get detailed description for a LangGraph node.

    Args:
        node_name: Internal node name

    Returns:
        Human-readable description
    """
    return NODE_STEP_DESCRIPTIONS.get(node_name, "Əməliyyat icra olunur...")


async def create_step_for_node(node_name: str) -> cl.Step:
    """Create a Chainlit step for a LangGraph node execution.

    Args:
        node_name: The LangGraph node being executed

    Returns:
        Chainlit Step object
    """
    label = get_step_label(node_name)

    step = cl.Step(
        name=label,
        type="tool" if node_name in ["nl_to_sql", "sql_executor", "vision_to_action"] else "llm",
        show_input=False,  # Don't clutter UI with raw state
    )

    await step.send()
    return step


async def update_step_output(step: cl.Step, output: str, status: str = "done"):
    """Update step with output and mark as done.

    Args:
        step: The step to update
        output: Output message to display
        status: Step status ("done", "error")
    """
    step.output = output

    if status == "error":
        step.is_error = True

    await step.update()


def with_step_visualization(node_name: str):
    """Decorator to wrap LangGraph node with Chainlit step visualization.

    Usage:
        @with_step_visualization("agronomist")
        async def agronomist_node(state: AgentState) -> dict[str, Any]:
            # Node implementation
            return updates

    Args:
        node_name: The name of the node (for labeling)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if we're in a Chainlit context
            try:
                cl.context.current_step
                in_chainlit = True
            except Exception:
                in_chainlit = False

            if not in_chainlit:
                # Not in Chainlit, execute normally
                return await func(*args, **kwargs)

            # Create step for this node
            step = await create_step_for_node(node_name)

            try:
                # Execute the node
                result = await func(*args, **kwargs)

                # Extract key info for step output
                output_summary = _summarize_node_output(node_name, result)
                await update_step_output(step, output_summary, "done")

                return result

            except Exception as e:
                # Show error in step
                await update_step_output(step, f"❌ Xəta: {str(e)}", "error")
                raise

        return wrapper

    return decorator


def _summarize_node_output(node_name: str, result: dict[str, Any]) -> str:
    """Create a human-readable summary of node output.

    Args:
        node_name: The node that produced the output
        result: The node's return value (state updates)

    Returns:
        Summary string for the step UI
    """
    if node_name == "supervisor":
        intent = result.get("intent", "unknown")
        confidence = result.get("intent_confidence", 0.0)
        return f"Niyyət: {intent} ({confidence:.1%} əminlik)"

    elif node_name == "context_loader":
        loaded = []
        if result.get("farm_context"):
            loaded.append("təsərrüfat")
        if result.get("weather_context"):
            loaded.append("hava")
        if result.get("user_context"):
            loaded.append("istifadəçi")
        return f"Yükləndi: {', '.join(loaded) if loaded else 'heç nə'}"

    elif node_name == "agronomist":
        response_len = len(result.get("current_response", ""))
        return f"Məsləhət hazırlandı ({response_len} simvol)"

    elif node_name == "weather":
        response_len = len(result.get("current_response", ""))
        return f"Hava məlumatı hazırlandı ({response_len} simvol)"

    elif node_name == "nl_to_sql":
        sql = result.get("sql_query", "")
        return f"SQL sorğusu:\n```sql\n{sql}\n```" if sql else "Sorğu hazırlanmadı"

    elif node_name == "sql_executor":
        rows = len(result.get("sql_results", []))
        return f"Nəticə: {rows} sətir tapıldı"

    elif node_name == "vision_to_action":
        response_len = len(result.get("current_response", ""))
        return f"Şəkil təhlili tamamlandı ({response_len} simvol)"

    elif node_name == "validator":
        alerts = result.get("alerts", [])
        if alerts:
            return f"⚠️ {len(alerts)} xəbərdarlıq tapıldı"
        return "✅ Yoxlama uğurlu"

    # Default
    return "✓ Tamamlandı"


async def show_thinking_process_step(message: str, details: str = ""):
    """Show a standalone step for thinking/processing.

    Useful for long operations that don't map to a specific node.

    Args:
        message: Step label
        details: Additional details to show in step
    """
    step = cl.Step(name=message, type="tool", show_input=False)
    await step.send()

    if details:
        step.output = details
        await step.update()

    return step
