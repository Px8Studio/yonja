# src/ALİM/agent/nodes/weather.py
"""Weather analyst node for weather-related queries.

Provides weather analysis and recommendations based on current
and forecasted weather conditions.
"""

from typing import Any

import structlog
from langchain_core.runnables import RunnableConfig

from alim.agent.state import AgentState, add_assistant_message
from alim.llm.factory import get_llm_from_config
from alim.llm.providers.base import LLMMessage

logger = structlog.get_logger(__name__)

# ============================================================
# Weather Analysis Prompt
# ============================================================

WEATHER_SYSTEM_PROMPT = """Sən Azərbaycan fermerləri üçün hava analitikisən.

SƏNİN VƏZİFƏN:
- Hava məlumatlarını fermerlər üçün izah et
- Kənd təsərrüfatı işlərinə təsirini qiymətləndir
- Konkret tövsiyələr ver

DİL QAYDALARI:
- Yalnız Azərbaycan dilində danış
- Türk sözləri işlətmə (eylül → Sentyabr, sulama → suvarma)
- Ayların adları: Yanvar, Fevral, Mart, Aprel, May, İyun, İyul, Avqust, Sentyabr, Oktyabr, Noyabr, Dekabr

CAVAB FORMATI:
📊 **Hava Vəziyyəti**:
[Cari hava məlumatları]

🌱 **Kənd Təsərrüfatına Təsiri**:
[Əkinə, suvarmaya, yığıma təsiri]

✅ **Tövsiyələr**:
1. [Konkret tövsiyə 1]
2. [Konkret tövsiyə 2]
3. [Konkret tövsiyə 3]
"""


def build_weather_context(state: AgentState) -> str:
    """Build weather context for the prompt."""
    weather = state.get("weather")
    farm_context = state.get("farm_context")

    parts = []

    if weather:
        parts.append(
            f"""CARİ HAVA:
- Temperatur: {weather.temperature_c}°C
- Rütubət: {weather.humidity_percent}%
- Yağış: {weather.precipitation_mm} mm
- Külək: {weather.wind_speed_kmh} km/saat
- Proqnoz: {weather.forecast_summary}"""
        )

    if farm_context:
        parts.append(
            f"""TƏSƏRRÜFAT:
- Region: {farm_context.region}
- Sahə: {farm_context.total_area_ha} hektar"""
        )

        if farm_context.active_crops:
            crops = ", ".join(c["crop"] for c in farm_context.active_crops[:5])
            parts.append(f"- Aktiv məhsullar: {crops}")

    return "\n\n".join(parts)


# ============================================================
# Weather Node
# ============================================================


async def weather_node(state: AgentState, config: RunnableConfig | None = None) -> dict[str, Any]:
    """Weather analyst node.

    Analyzes weather conditions and provides farming-related
    weather advice.

    Args:
        state: Current agent state
        config: RunnableConfig with metadata (including model override from Chat Profiles)

    Returns:
        State updates with weather analysis
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("weather")

    user_input = state.get("current_input", "")
    intent = state.get("intent")
    weather = state.get("weather")

    logger.info(
        "weather_node_start",
        message=user_input[:100],
        has_weather_data=bool(weather),
        temperature=weather.temperature_c if weather else None,
    )

    # Build messages
    weather_context = build_weather_context(state)

    full_system = WEATHER_SYSTEM_PROMPT
    if weather_context:
        full_system += f"\n\n<KONTEKST>\n{weather_context}\n</KONTEKST>"

    messages = [
        LLMMessage.system(full_system),
        LLMMessage.user(user_input),
    ]

    # Generate response using runtime model selection
    provider = get_llm_from_config(config)

    try:
        response = await provider.generate(
            messages,
            temperature=0.5,
            max_tokens=600,
        )

        response_text = response.content.strip()

        # Add weather-specific alerts if temperature is extreme
        weather = state.get("weather")
        if weather:
            alerts_to_add = []

            if weather.temperature_c and weather.temperature_c < 0:
                alerts_to_add.append(
                    {
                        "alert_type": "frost_warning",
                        "severity": "high",
                        "message_az": f"⚠️ Şaxta xəbərdarlığı! Temperatur {weather.temperature_c}°C",
                    }
                )
            elif weather.temperature_c and weather.temperature_c > 35:
                alerts_to_add.append(
                    {
                        "alert_type": "heat_warning",
                        "severity": "high",
                        "message_az": f"⚠️ İsti xəbərdarlığı! Temperatur {weather.temperature_c}°C - suvarma artırın",
                    }
                )

            if weather.precipitation_mm and weather.precipitation_mm > 20:
                alerts_to_add.append(
                    {
                        "alert_type": "heavy_rain",
                        "severity": "medium",
                        "message_az": f"🌧️ Güclü yağış gözlənilir ({weather.precipitation_mm}mm)",
                    }
                )

            if alerts_to_add:
                logger.info(
                    "weather_node_complete",
                    response_length=len(response_text),
                    alerts_count=len(alerts_to_add),
                )
                return {
                    "current_response": response_text,
                    "nodes_visited": nodes_visited,
                    "messages": [add_assistant_message(state, response_text, "weather", intent)],
                    "alerts": alerts_to_add,
                }

        logger.info(
            "weather_node_complete",
            response_length=len(response_text),
            alerts_count=0,
        )

        return {
            "current_response": response_text,
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, response_text, "weather", intent)],
        }

    except Exception as e:
        logger.error(
            "weather_node_error",
            error=str(e),
        )
        error_response = (
            "Hava məlumatlarını yükləyərkən xəta baş verdi. Zəhmət olmasa sonra yenidən cəhd edin."
        )

        return {
            "current_response": error_response,
            "error": str(e),
            "nodes_visited": nodes_visited,
            "messages": [add_assistant_message(state, error_response, "weather", intent)],
        }
