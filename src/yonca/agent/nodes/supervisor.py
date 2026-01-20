# src/yonca/agent/nodes/supervisor.py
"""Supervisor node for routing user messages to specialist agents.

The Supervisor is the entry point for all user messages. It:
1. Classifies the user's intent
2. Determines which specialist agent should handle it
3. Decides what context needs to be loaded
"""

import json
import re
from typing import Any

from yonca.agent.state import (
    AgentState,
    RoutingDecision,
    UserIntent,
    add_assistant_message,
)
from yonca.config import settings
from yonca.llm.factory import get_llm_provider
from yonca.llm.providers.base import LLMMessage


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
    UserIntent.GREETING: "end",  # Handled directly in supervisor_node
    UserIntent.GENERAL_ADVICE: "agronomist",
    UserIntent.OFF_TOPIC: "end",  # Handled directly in supervisor_node
    UserIntent.CLARIFICATION: "end",  # Needs clarification, ask user to be more specific
    UserIntent.DATA_QUERY: "nl_to_sql",
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
    "Salam! Mən Yonca AI - sizin kənd təsərrüfatı köməkçinizəm. Sizə necə kömək edə bilərəm?",
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

async def classify_intent(user_input: str) -> tuple[UserIntent, float, str]:
    """Classify the user's intent using LLM.
    
    Args:
        user_input: The user's message
        
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
    if any(word in input_lower for word in [
        "sql", "select", "verilənlər bazası", "sorgu", "query", "cədvəl", "filter",
        "parsel", "parcel", "farm", "məlumat bazası"
    ]):
        return UserIntent.DATA_QUERY, 0.88, "Verilənlər bazası sorğusu aşkarlandı"
    
    # For more complex classification, use LLM
    provider = get_llm_provider()
    
    messages = [
        LLMMessage.system(INTENT_CLASSIFICATION_PROMPT),
        LLMMessage.user(user_input),
    ]
    
    try:
        response = await provider.generate(messages, temperature=0.1, max_tokens=200)
        
        # Parse JSON response
        content = response.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
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
            
    except Exception as e:
        # Fallback on error
        pass
    
    return UserIntent.GENERAL_ADVICE, 0.5, "Standart təsnifat (LLM xətası)"


async def supervisor_node(state: AgentState) -> dict[str, Any]:
    """Supervisor node - routes messages to appropriate handlers.
    
    This is the entry point for all user messages. It:
    1. Classifies the intent
    2. Handles simple cases (greetings, off-topic) directly
    3. Routes complex cases to specialist nodes
    
    Args:
        state: Current agent state
        
    Returns:
        State updates with routing decision
    """
    user_input = state.get("current_input", "")
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("supervisor")
    
    # Classify intent
    intent, confidence, reasoning = await classify_intent(user_input)
    
    # Determine target node
    target_node = INTENT_TO_NODE.get(intent, "agronomist")
    requires_context = INTENT_REQUIRES_CONTEXT.get(intent, [])
    
    # Handle simple cases directly
    if intent == UserIntent.GREETING:
        import random
        response = random.choice(GREETING_RESPONSES)
        
        return {
            "routing": RoutingDecision(
                target_node="end",
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
            ),
            "intent": intent,
            "intent_confidence": confidence,
            "current_response": response,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, response, "supervisor", intent)],
        }
    
    if intent == UserIntent.OFF_TOPIC:
        return {
            "routing": RoutingDecision(
                target_node="end",
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
            ),
            "intent": intent,
            "intent_confidence": confidence,
            "current_response": OFF_TOPIC_RESPONSE,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, OFF_TOPIC_RESPONSE, "supervisor", intent)],
        }
    
    if intent == UserIntent.CLARIFICATION:
        clarification_response = (
            "Zəhmət olmasa daha konkret ola bilərsinizmi? "
            "Məsələn, hansı məhsul haqqında soruşursunuz və ya hansı mövzuda məlumat lazımdır?"
        )
        return {
            "routing": RoutingDecision(
                target_node="end",
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
            ),
            "intent": intent,
            "intent_confidence": confidence,
            "current_response": clarification_response,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, clarification_response, "supervisor", intent)],
        }
    
    # Route to specialist
    return {
        "routing": RoutingDecision(
            target_node=target_node,
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            requires_context=requires_context,
        ),
        "intent": intent,
        "intent_confidence": confidence,
        "nodes_visited": nodes_visited,
    }


# ============================================================
# Conditional Edge Functions
# ============================================================

def route_from_supervisor(state: AgentState) -> str:
    """Determine next node based on supervisor's routing decision.
    
    Used as a conditional edge in the graph.
    """
    routing = state.get("routing")
    
    if routing is None:
        return "agronomist"  # Default
    
    # If response already generated (greeting/off-topic), end
    if routing.target_node == "end":
        return "end"
    
    # Check if context loading is needed
    if routing.requires_context:
        return "context_loader"
    
    return routing.target_node
