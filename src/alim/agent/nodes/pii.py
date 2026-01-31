from typing import Any

from alim.agent.state import AgentState
from alim.security.pii_gateway import get_pii_gateway


async def pii_masking_node(state: AgentState) -> dict[str, Any]:
    """Node to mask PII from user input before it reaches the rest of the graph.

    This ensures that:
    1. Sensitive data (FIN, Phone, etc.) is replaced with placeholders.
    2. clean input is passed to the LLM agent.
    3. Langreuse traces contain only the masked input for the start of the trace.
    """
    user_input = state.get("user_input", "")
    gateway = get_pii_gateway()

    # Check if we need to mask
    if not user_input:
        return {}

    result = gateway.strip_pii(user_input)

    if result.has_pii:
        # Return updated user_input used by downstream nodes
        return {
            "user_input": result.cleaned_text,
            "alerts": state.get("alerts", [])
            + [
                {
                    "type": "info",
                    "message": f"PII detected and masked: {', '.join(result.pii_types_found)}",
                }
            ],
        }

    return {}
