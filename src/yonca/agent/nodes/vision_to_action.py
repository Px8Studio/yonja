# src/yonca/agent/nodes/vision_to_action.py
"""Vision-to-Action node.

Analyzes uploaded images (paths provided in state under 'images') and
proposes actionable recommendations (e.g., pest detection, irrigation hints).
Currently, this is text-only due to multimodal transport constraints.
It summarizes intent and produces a farmer-facing action plan.
"""

from typing import Any

from yonca.agent.state import AgentState, add_assistant_message, UserIntent
from yonca.llm.inference_engine import InferenceEngine
from yonca.llm.providers.base import LLMMessage

SYSTEM_PROMPT = (
    "Sən aqronomik görüntü analiz köməkçisisən. İstifadəçi tərəfindən "
    "yüklənmiş şəkillərin təsviri əsasında təsir planı hazırla. "
    "Cavabda:\n"
    "- Müşahidə: qısa təsvir\n"
    "- Risk: ehtimal olunan problem (həşərat, xəstəlik, suvarma çatışmazlığı)\n"
    "- Tövsiyə: konkret ediləcək addımlar (48 saatlıq plan)\n"
    "- Xəbərdarlıq: ehtiyac varsa xəbərdarlıq səviyyəsi (LOW/MEDIUM/HIGH)\n"
    "Azerbaycan dilində, səlis və praktik yaz."
)

async def vision_to_action_node(state: AgentState) -> dict[str, Any]:
    """Propose actions based on image descriptions.

    Args:
        state: Current agent state
    Returns:
        Updates with 'current_response' containing the action plan.
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("vision_to_action")

    # NOTE: For now, we only read a textual hint. Future: multimodal payloads.
    image_note = "(Şəkil faylları UI tərəfindən yüklənib; gələcəkdə multimodal analiz)"

    engine = InferenceEngine()
    messages = [
        LLMMessage.system(SYSTEM_PROMPT),
        LLMMessage.user(f"Şəkil təsviri: {image_note}. İstifadəçi mesajı: " + state.get("current_input", "")),
    ]

    try:
        resp = await engine.generate(messages, temperature=0.1, max_tokens=400)
        content = resp.content.strip()
        return {
            "current_response": content,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, content, "vision_to_action", UserIntent.VISION_ANALYSIS)],
        }
    except Exception:
        msg = "Şəkil analizi zamanı xəta baş verdi"
        return {
            "error": msg,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, msg, "vision_to_action", UserIntent.VISION_ANALYSIS)],
        }
