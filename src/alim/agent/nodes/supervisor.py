# src/ALİM/agent/nodes/supervisor.py
"""Supervisor node for routing user messages to specialist agents.

The Supervisor is the entry point for all user messages. It:
1. Classifies the user's intent
2. Determines which specialist agent should handle it
3. Decides what context needs to be loaded
"""

import json
import re

import structlog
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from alim.agent.state import (
    AgentState,
    RoutingDecision,
    UserIntent,
    add_assistant_message,
)
from alim.llm.factory import get_llm_from_config
from alim.llm.providers.base import LLMMessage

logger = structlog.get_logger(__name__)

# ============================================================
# Intent Classification Prompt
# ============================================================

INTENT_CLASSIFICATION_PROMPT = """Sən istifadəçi mesajlarını təsnif edən köməkçisən.

İstifadəçinin mesajını aşağıdakı kateqoriyalardan birinə aid et:

KATEQORIYALAR:
- irrigation: Suvarma ilə bağlı suallar (su, suvarma cədvəli, damcı suvarma)
- fertilization: Gübrələmə ilə bağlı suallar (gübrə, azot, fosfor, kalium)
- pest_control: Zərərverici və xəstəliklərlə bağlı suallar (həşərat, göbələk, virus)
- harvest: Məhsul yığımı ilə bağlı suallar (yığım vaxtı, saxlama)
- planting: Əkin ilə bağlı suallar (toxum, əkin vaxtı, şitil)
- crop_rotation: Növbəli əkin ilə bağlı suallar (torpaq bərpası, rotasiya)
- weather: Hava ilə bağlı suallar (temperatur, yağış, proqnoz)
- greeting: Salamlama (salam, necəsən)
- general_advice: Ümumi kənd təsərrüfatı məsləhəti
- off_topic: Kənd təsərrüfatı ilə əlaqəsi olmayan mövzu
- clarification: Daha çox məlumat lazımdır
 - data_query: Verilənlər bazası sorğuları (SQL, cədvəl, filter, SELECT)

CAVAB FORMATI (JSON):
{
  "intent": "kateqoriya_adı",
  "confidence": 0.95,
  "reasoning": "Qısa izahat"
}

İSTİFADƏÇİ MESAJI:
"""


# ============================================================
# Routing Rules
# ============================================================

INTENT_TO_NODE = {
    UserIntent.IRRIGATION: "agronomist",
    UserIntent.FERTILIZATION: "agronomist",
    UserIntent.PEST_CONTROL: "agronomist",
    UserIntent.HARVEST: "agronomist",
    UserIntent.PLANTING: "agronomist",
    UserIntent.CROP_ROTATION: "agronomist",
    UserIntent.WEATHER: "weather",
    UserIntent.GREETING: END,  # Handled directly in supervisor_node
    UserIntent.GENERAL_ADVICE: "agronomist",
    UserIntent.OFF_TOPIC: END,  # Handled directly in supervisor_node
    UserIntent.CLARIFICATION: END,  # Needs clarification, ask user to be more specific
    UserIntent.DATA_QUERY: "nl_to_sql",
    UserIntent.VISION_ANALYSIS: "vision_to_action",
}

INTENT_REQUIRES_CONTEXT = {
    UserIntent.IRRIGATION: ["farm", "weather"],
    UserIntent.FERTILIZATION: ["farm"],
    UserIntent.PEST_CONTROL: ["farm", "weather"],
    UserIntent.HARVEST: ["farm", "weather"],
    UserIntent.PLANTING: ["farm", "weather"],
    UserIntent.CROP_ROTATION: ["farm"],
    UserIntent.WEATHER: ["farm", "weather"],
    UserIntent.GENERAL_ADVICE: ["farm"],
    UserIntent.DATA_QUERY: ["farm"],
}


# ============================================================
# Greeting Responses
# ============================================================

GREETING_RESPONSES = [
    "Salam! Mən ALİM - sizin kənd təsərrüfatı köməkçinizəm. Sizə necə kömək edə bilərəm?",
    "Salam, əziz fermer! Bugün sizə hansı sahədə yardımçı ola bilərəm?",
    "Xoş gördük! Suvarma, gübrələmə, və ya digər aqrar məsələlərdə sizə kömək etməyə hazıram.",
]

OFF_TOPIC_RESPONSE = (
    "Təəssüf ki, bu mövzu kənd təsərrüfatı ilə əlaqəli deyil. "
    "Mən yalnız aqrar məsələlərdə - suvarma, gübrələmə, əkin, məhsul yığımı "
    "və s. mövzularda kömək edə bilərəm. Başqa bir sualınız varmı?"
)


# ============================================================
# Supervisor Node
# ============================================================


async def classify_intent(
    user_input: str, config: RunnableConfig | None = None
) -> tuple[UserIntent, float, str]:
    """Classify the user's intent using LLM.

    Args:
        user_input: The user's message
        config: RunnableConfig with metadata (including model override)

    Returns:
        Tuple of (intent, confidence, reasoning)
    """
    # Quick pattern matching for common intents
    input_lower = user_input.lower()

    # Greeting patterns
    if any(word in input_lower for word in ["salam", "necəsən", "xoş gördük", "sağ ol"]):
        return UserIntent.GREETING, 0.95, "Salamlama sözləri aşkarlandı"

    # Weather patterns
    if any(word in input_lower for word in ["hava", "temperatur", "yağış", "proqnoz", "dərəcə"]):
        return UserIntent.WEATHER, 0.90, "Hava ilə bağlı sözlər aşkarlandı"

    # Data query / SQL patterns
    if any(
        word in input_lower
        for word in [
            "sql",
            "select",
            "verilənlər bazası",
            "sorgu",
            "query",
            "cədvəl",
            "filter",
            "parsel",
            "parcel",
            "farm",
            "məlumat bazası",
        ]
    ):
        return UserIntent.DATA_QUERY, 0.88, "Verilənlər bazası sorğusu aşkarlandı"

    # For more complex classification, use LLM
    # Use get_llm_from_config to respect runtime model selection (e.g., from Chat Profiles)
    provider = get_llm_from_config(config)

    messages = [
        LLMMessage.system(INTENT_CLASSIFICATION_PROMPT),
        LLMMessage.user(user_input),
    ]

    try:
        response = await provider.generate(messages, temperature=0.1, max_tokens=200)

        # Parse JSON response
        content = response.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[^}]+\}", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())

            intent_str = data.get("intent", "general_advice")
            confidence = data.get("confidence", 0.5)
            reasoning = data.get("reasoning", "")

            # Map string to enum
            try:
                intent = UserIntent(intent_str)
            except ValueError:
                intent = UserIntent.GENERAL_ADVICE

            return intent, confidence, reasoning

    except Exception:
        # Fallback on error
        pass

    return UserIntent.GENERAL_ADVICE, 0.5, "Standart təsnifat (LLM xətası)"


async def supervisor_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """Supervisor node - routes messages to appropriate handlers.

    This is the entry point for all user messages. It:
    1. Classifies the intent
    2. Determines routing (but lets graph.py handle the edge)

    Args:
        state: Current agent state
        config: RunnableConfig with metadata

    Returns:
        State updates (routing decision, intent, response for simple cases)
    """
    user_input = state.get("current_input", "")
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("supervisor")

    # Classify intent
    intent, confidence, reasoning = await classify_intent(user_input, config)

    logger.info(
        "supervisor_node_process",
        intent=intent.value if intent else "unknown",
        confidence=confidence,
    )

    updates = {
        "intent": intent,
        "intent_confidence": confidence,
        "nodes_visited": nodes_visited,
    }

    # Handle simple cases directly (generating response but not ending flow here)
    if intent == UserIntent.GREETING:
        import random

        response = random.choice(GREETING_RESPONSES)
        updates["current_response"] = response
        updates["messages"] = [add_assistant_message(state, response, "supervisor", intent)]
        # Routing: End immediately
        updates["routing"] = RoutingDecision(
            target_node="end",
            intent=intent,
            confidence=confidence,
            reasoning="Greeting handled directly",
        )
        return updates

    if intent == UserIntent.OFF_TOPIC:
        updates["current_response"] = OFF_TOPIC_RESPONSE
        updates["messages"] = [
            add_assistant_message(state, OFF_TOPIC_RESPONSE, "supervisor", intent)
        ]
        updates["routing"] = RoutingDecision(
            target_node="end",
            intent=intent,
            confidence=confidence,
            reasoning="Off-topic handled directly",
        )
        return updates

    if intent == UserIntent.CLARIFICATION:
        response = "Zəhmət olmasa daha konkret ola bilərsinizmi?"
        updates["current_response"] = response
        updates["messages"] = [add_assistant_message(state, response, "supervisor", intent)]
        updates["routing"] = RoutingDecision(
            target_node="end",
            intent=intent,
            confidence=confidence,
            reasoning="Clarification requested",
        )
        return updates

    # Complex cases: Determine required context and next step
    requires_context = INTENT_REQUIRES_CONTEXT.get(intent, [])

    # Determine target subgraph
    target_node = "specialist_subgraph"
    if intent == UserIntent.DELETE_PARCEL:
        target_node = "hitl_subgraph"

    # Update routing decision
    updates["routing"] = RoutingDecision(
        target_node=target_node,
        intent=intent,
        confidence=confidence,
        reasoning=reasoning,
        requires_context=requires_context,
    )

    return updates
