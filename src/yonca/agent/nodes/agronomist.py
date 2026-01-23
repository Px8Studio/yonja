# src/yonca/agent/nodes/agronomist.py
"""Agronomist agent node for farming advice.

The main specialist agent that provides agricultural recommendations
for irrigation, fertilization, pest control, planting, and harvesting.
"""

from datetime import UTC
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from yonca.agent.state import AgentState, UserIntent, add_assistant_message
from yonca.llm.factory import get_llm_from_config
from yonca.llm.providers.base import LLMMessage

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# ============================================================
# Prompt Templates
# ============================================================


def load_system_prompt() -> str:
    """Load the master system prompt from file."""
    prompt_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / "prompts"
        / "system"
        / "master_v1.0.0_az_strict.txt"
    )

    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    # Fallback inline prompt
    return """Sən "Yonca AI" adlı Azərbaycan fermerlərinə kömək edən süni intellekt köməkçisisən.
Yalnız Azərbaycan dilində cavab ver. Türk dilindən sözlər işlətmə.
Konkret və praktiki məsləhət ver."""


def build_context_prompt(state: AgentState) -> str:
    """Build context section from loaded farm/user data."""
    parts = []

    # User context
    user_context = state.get("user_context")
    if user_context:
        experience_map = {
            "novice": "təzə başlayan",
            "intermediate": "orta səviyyəli",
            "expert": "təcrübəli",
        }
        exp_level = experience_map.get(user_context.experience_level, user_context.experience_level)
        parts.append(
            f"""<İSTİFADƏÇİ>
Ad: {user_context.display_name}
Təcrübə: {exp_level}
Təsərrüfat sayı: {user_context.farm_count}
Ümumi sahə: {user_context.total_area_ha:.1f} hektar
</İSTİFADƏÇİ>"""
        )

    # Farm context
    farm_context = state.get("farm_context")
    if farm_context:
        crops_info = ""
        if farm_context.active_crops:
            crops = [
                f"- {c['crop']} ({c['parcel_id']}, {c['days_since_sowing']} gün)"
                for c in farm_context.active_crops[:5]
            ]
            crops_info = "\nAktiv məhsullar:\n" + "\n".join(crops)

        parts.append(
            f"""<TƏSƏRRÜFAT>
Ad: {farm_context.farm_name}
Region: {farm_context.region}
Tip: {farm_context.farm_type}
Sahə: {farm_context.total_area_ha:.1f} hektar
Sahə sayı: {farm_context.parcel_count}{crops_info}
</TƏSƏRRÜFAT>"""
        )

    # Weather context
    weather = state.get("weather")
    if weather:
        parts.append(
            f"""<HAVA>
Temperatur: {weather.temperature_c}°C
Rütubət: {weather.humidity_percent}%
Yağış: {weather.precipitation_mm} mm
Külək: {weather.wind_speed_kmh} km/saat
Proqnoz: {weather.forecast_summary}
</HAVA>"""
        )

    # Alerts
    alerts = state.get("alerts", [])
    if alerts:
        alert_lines = [f"- [{a['severity'].upper()}] {a['message_az']}" for a in alerts[:3]]
        parts.append(
            f"""<XƏBƏRDARLIQLAR>
{chr(10).join(alert_lines)}
</XƏBƏRDARLIQLAR>"""
        )

    return "\n\n".join(parts) if parts else ""


def build_intent_prompt(intent: UserIntent | None) -> str:
    """Build intent-specific guidance for the response."""
    prompts = {
        UserIntent.IRRIGATION: """SUVARMA MƏSLƏHƏTI:
- Torpaq nəmliyi və bitki ehtiyacını qiymətləndir
- Suvarma cədvəli təklif et
- Su qənaəti yollarını göstər""",
        UserIntent.FERTILIZATION: """GÜBRƏLƏMƏ MƏSLƏHƏTI:
- Torpaq analizinə əsaslanmağı tövsiyə et
- Gübrə növlərini izah et (azot, fosfor, kalium)
- Dozaj və vaxtlama barədə məsləhət ver""",
        UserIntent.PEST_CONTROL: """ZƏRƏRVERİCİ MÜBARİZƏSİ:
- Əlamətləri soruş (varsa)
- Bioloji və kimyəvi mübarizə üsullarını təklif et
- Profilaktika tövsiyə et""",
        UserIntent.HARVEST: """MƏHSUL YIĞIMI:
- Yetişmə əlamətlərini izah et
- Optimal yığım vaxtını müəyyən et
- Saxlama tövsiyələri ver""",
        UserIntent.PLANTING: """ƏKİN MƏSLƏHƏTI:
- Torpaq hazırlığını izah et
- Əkin vaxtını tövsiyə et
- Toxum seçimi barədə məsləhət ver""",
        UserIntent.CROP_ROTATION: """NÖVBƏLİ ƏKİN:
- Torpaq sağlamlığını izah et
- Uyğun rotasiya sxemi təklif et
- Faydalarını göstər""",
    }

    return prompts.get(intent, "")


# ============================================================
# Agronomist Node
# ============================================================


async def agronomist_node(
    state: AgentState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """Agronomist specialist node.

    Generates agricultural advice based on:
    - User's intent (irrigation, fertilization, etc.)
    - Farm context (crops, region, soil)
    - Weather conditions
    - Agronomy rules (from validator)

    Args:
        state: Current agent state with context loaded
        config: RunnableConfig with metadata (including model override from Chat Profiles)

    Returns:
        State updates with generated response
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("agronomist")

    user_input = state.get("current_input", "")
    intent = state.get("intent")
    conversation_context = state.get("conversation_context", {})

    logger.info(
        "agronomist_node_start",
        message=user_input[:100],
        intent=intent.value if intent else "unknown",
        has_farm_context=bool(state.get("farm_context")),
        has_weather=bool(state.get("weather")),
        conversation_stage=conversation_context.get("conversation_stage"),
    )

    # Build the full prompt
    system_prompt = load_system_prompt()
    context_prompt = build_context_prompt(state)
    intent_guidance = build_intent_prompt(intent)

    # Combine prompts
    full_system = system_prompt
    if context_prompt:
        full_system += f"\n\n<KONTEKST>\n{context_prompt}\n</KONTEKST>"
    if intent_guidance:
        full_system += f"\n\n{intent_guidance}"

    # Phase 4.2: Evaluate ZekaLab MCP rules based on intent and include summary
    mcp_section = ""
    mcp_traces = list(state.get("mcp_traces", []))
    try:
        from yonca.mcp.handlers import get_zekalab_handler

        handler = await get_zekalab_handler()

        farm_ctx = state.get("farm_context")
        weather = state.get("weather")
        active_crop = None
        if farm_ctx and getattr(farm_ctx, "active_crops", None):
            active_crop = farm_ctx.active_crops[0] if farm_ctx.active_crops else None

        # Prepare common fields
        farm_id = getattr(farm_ctx, "farm_id", None)
        crop_type = (active_crop.get("crop") if isinstance(active_crop, dict) else None) or "wheat"
        soil_type = "loamy"
        temperature_c = getattr(weather, "temperature_c", 25.0)
        humidity_percent = getattr(weather, "humidity_percent", 60.0)
        rainfall_mm = getattr(weather, "precipitation_mm", 0.0)
        growth_days = (
            active_crop.get("days_since_sowing") if isinstance(active_crop, dict) else 0
        ) or 0

        mcp_results: list[tuple[str, dict]] = []

        if intent == UserIntent.IRRIGATION and farm_id:
            result, trace = await handler.evaluate_irrigation_rules(
                farm_id=farm_id,
                crop_type=crop_type,
                soil_type=soil_type,
                current_soil_moisture_percent=45.0,
                temperature_c=temperature_c,
                rainfall_mm_last_7_days=rainfall_mm,
                growth_stage_days=growth_days,
            )
            mcp_traces.append(trace.dict())
            mcp_results.append(("Suvarma", result))

        elif intent == UserIntent.FERTILIZATION and farm_id:
            result, trace = await handler.evaluate_fertilization_rules(
                farm_id=farm_id,
                crop_type=crop_type,
                soil_type=soil_type,
                soil_nitrogen_ppm=None,
                soil_phosphorus_ppm=None,
                soil_potassium_ppm=None,
                growth_stage_days=growth_days,
            )
            mcp_traces.append(trace.dict())
            mcp_results.append(("Gübrələmə", result))

        elif intent == UserIntent.PEST_CONTROL and farm_id:
            result, trace = await handler.evaluate_pest_control_rules(
                farm_id=farm_id,
                crop_type=crop_type,
                temperature_c=temperature_c,
                humidity_percent=humidity_percent,
                observed_pests=[],
                growth_stage_days=growth_days,
                rainfall_mm_last_3_days=rainfall_mm,
            )
            mcp_traces.append(trace.dict())
            mcp_results.append(("Zərərverici nəzarəti", result))

        elif intent == UserIntent.HARVEST and farm_id:
            from datetime import datetime, timedelta

            planting_date = (datetime.now(UTC) - timedelta(days=growth_days)).date().isoformat()

            result, trace = await handler.predict_harvest_date(
                farm_id=farm_id,
                crop_type=crop_type,
                planting_date=planting_date,
                current_gdd_accumulated=0,
            )
            mcp_traces.append(trace.dict())
            mcp_results.append(("Məhsul yığımı", result))

        # Build MCP rule summary section
        if mcp_results:
            lines = []
            for title, res in mcp_results:
                if intent == UserIntent.IRRIGATION:
                    lines.append(
                        f"{title}: tövsiyə olunan su {res.get('recommended_water_mm', 0)} mm; vaxt: {res.get('timing', 'uyğun')}"
                    )
                elif intent == UserIntent.FERTILIZATION:
                    lines.append(
                        f"{title}: N {res.get('nitrogen_kg_per_hectare', 0)} kg/ha, P {res.get('phosphorus_kg_per_hectare', 0)} kg/ha, K {res.get('potassium_kg_per_hectare', 0)} kg/ha"
                    )
                elif intent == UserIntent.PEST_CONTROL:
                    lines.append(
                        f"{title}: tövsiyə olunan üsul {res.get('method', 'uyğun')}; hərəkət: {res.get('recommended_action', 'tətbiq et')}"
                    )
                elif intent == UserIntent.HARVEST:
                    lines.append(
                        f"{title}: gözlənilən tarix {res.get('predicted_harvest_date', 'naməlum')} (təxmini gün: {res.get('days_to_harvest_estimate', '—')})"
                    )

            mcp_section = "\n\n<MCP_QAYDALAR>\n" + "\n".join(lines) + "\n</MCP_QAYDALAR>"

    except Exception as e:
        logger.warning("agronomist_mcp_warning", error=str(e))

    if mcp_section:
        full_system += mcp_section
        if mcp_traces:
            # Store traces back into state for observability
            state["mcp_traces"] = mcp_traces

    # Build conversation history
    messages = [LLMMessage.system(full_system)]

    # Add recent conversation for context
    conversation = state.get("messages", [])
    for msg in conversation[-6:]:  # Last 3 turns
        if isinstance(msg, HumanMessage):
            messages.append(LLMMessage.user(msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(LLMMessage.assistant(msg.content))

    # Generate response using runtime model selection
    provider = get_llm_from_config(config)

    try:
        response = await provider.generate(
            messages,
            temperature=0.7,
            max_tokens=800,
        )

        response_text = response.content.strip()

        # Check for rule-based additions
        matched_rules = state.get("matched_rules", [])
        if matched_rules:
            # Append rule-based recommendations
            rule_additions = []
            for rule in matched_rules[:2]:  # Top 2 rules
                rule_additions.append(
                    f"📋 {rule.get('rule_name', '')}: {rule.get('recommendation_az', '')}"
                )

            if rule_additions:
                response_text += "\n\n**Qayda əsaslı tövsiyələr:**\n" + "\n".join(rule_additions)

        return {
            "current_response": response_text,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, response_text, "agronomist", intent)],
        }

    except Exception as e:
        logger.error(
            "agronomist_node_error",
            error=str(e),
            intent=intent.value if intent else "unknown",
        )
        error_response = (
            "Bağışlayın, texniki problem yarandı. "
            "Zəhmət olmasa sualınızı bir az sonra təkrar yoxlayın."
        )

        return {
            "current_response": error_response,
            "error": str(e),
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, error_response, "agronomist", intent)],
        }


async def agronomist_node_streaming(state: AgentState, config: RunnableConfig | None = None):
    """Streaming version of agronomist node.

    Yields tokens as they are generated for real-time response.

    Args:
        state: Current agent state
        config: RunnableConfig with metadata (including model override from Chat Profiles)
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("agronomist")

    intent = state.get("intent")

    # Build prompts
    system_prompt = load_system_prompt()
    context_prompt = build_context_prompt(state)
    intent_guidance = build_intent_prompt(intent)

    full_system = system_prompt
    if context_prompt:
        full_system += f"\n\n<KONTEKST>\n{context_prompt}\n</KONTEKST>"
    if intent_guidance:
        full_system += f"\n\n{intent_guidance}"

    messages = [LLMMessage.system(full_system)]

    conversation = state.get("messages", [])
    for msg in conversation[-6:]:
        if isinstance(msg, HumanMessage):
            messages.append(LLMMessage.user(msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(LLMMessage.assistant(msg.content))

    # Use runtime model selection
    provider = get_llm_from_config(config)

    full_response = ""
    async for chunk in provider.stream(messages, temperature=0.7, max_tokens=800):
        full_response += chunk
        yield {"type": "token", "content": chunk}

    yield {
        "type": "final",
        "state_update": {
            "current_response": full_response,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, full_response, "agronomist", intent)],
        },
    }
