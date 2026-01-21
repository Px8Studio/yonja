# src/yonca/agent/nodes/validator.py
"""Validator node for rule-based checks.

Validates recommendations against agronomy rules before
returning to user. Ensures advice is safe and accurate.
"""

from typing import Any

import structlog

from yonca.agent.state import AgentState

logger = structlog.get_logger(__name__)

# ============================================================
# Validation Rules (Inline for MVP, will move to YAML)
# ============================================================

SAFETY_RULES = {
    # Dangerous temperature thresholds
    "extreme_cold": {
        "condition": lambda state: (
            state.get("weather")
            and state["weather"].temperature_c is not None
            and state["weather"].temperature_c < -5
        ),
        "warning_az": "⚠️ Xəbərdarlıq: Temperatur çox aşağıdır. Açıq havada işləmək təhlükəlidir.",
        "severity": "high",
    },
    "extreme_heat": {
        "condition": lambda state: (
            state.get("weather")
            and state["weather"].temperature_c is not None
            and state["weather"].temperature_c > 40
        ),
        "warning_az": "⚠️ Xəbərdarlıq: Temperatur həddindən artıq yüksəkdir. Günortadan qaçının.",
        "severity": "high",
    },
    # Heavy rain warning
    "heavy_rain": {
        "condition": lambda state: (
            state.get("weather")
            and state["weather"].precipitation_mm is not None
            and state["weather"].precipitation_mm > 30
        ),
        "warning_az": "🌧️ Güclü yağış gözlənilir. Drenaj sistemini yoxlayın.",
        "severity": "medium",
    },
}

AGRONOMIC_VALIDATIONS = {
    # Irrigation in rain
    "no_irrigation_in_rain": {
        "condition": lambda state: (
            state.get("intent")
            and state["intent"].value == "irrigation"
            and state.get("weather")
            and state["weather"].precipitation_mm is not None
            and state["weather"].precipitation_mm > 10
        ),
        "warning_az": "💧 Hazırda yağış yağır/gözlənilir. Suvarmanı təxirə salın.",
        "severity": "medium",
    },
    # Spraying in wind
    "no_spraying_in_wind": {
        "condition": lambda state: (
            state.get("intent")
            and state["intent"].value == "pest_control"
            and state.get("weather")
            and state["weather"].wind_speed_kmh is not None
            and state["weather"].wind_speed_kmh > 20
        ),
        "warning_az": "💨 Külək çox güclüdür. Dərman çiləməni küləksiz zamana keçirin.",
        "severity": "medium",
    },
    # Frost and planting
    "no_planting_in_frost": {
        "condition": lambda state: (
            state.get("intent")
            and state["intent"].value == "planting"
            and state.get("weather")
            and state["weather"].temperature_c is not None
            and state["weather"].temperature_c < 5
        ),
        "warning_az": "❄️ Temperatur əkin üçün çox aşağıdır. İstiləşməni gözləyin.",
        "severity": "high",
    },
}


# ============================================================
# Validator Node
# ============================================================


async def validator_node(state: AgentState) -> dict[str, Any]:
    """Validator node for rule-based checks.

    Checks the generated response against safety and agronomic rules.
    Adds warnings if any rules are triggered.

    This is a pass-through node that adds validation warnings
    without blocking the response.

    Args:
        state: Current agent state

    Returns:
        State updates with validation results
    """
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("validator")

    logger.info(
        "validator_node_start",
        has_response=bool(state.get("current_response")),
        intent=state.get("intent").value if state.get("intent") else "unknown",
    )

    matched_rules: list[dict] = []
    additional_warnings: list[str] = []

    # Check safety rules
    for rule_id, rule in SAFETY_RULES.items():
        try:
            if rule["condition"](state):
                matched_rules.append(
                    {
                        "rule_id": rule_id,
                        "rule_name": rule_id.replace("_", " ").title(),
                        "category": "safety",
                        "priority": rule["severity"],
                        "confidence": 1.0,
                        "recommendation_az": rule["warning_az"],
                    }
                )
                additional_warnings.append(rule["warning_az"])
        except Exception:
            pass  # Skip failed rule evaluations

    # Check agronomic rules
    for rule_id, rule in AGRONOMIC_VALIDATIONS.items():
        try:
            if rule["condition"](state):
                matched_rules.append(
                    {
                        "rule_id": rule_id,
                        "rule_name": rule_id.replace("_", " ").title(),
                        "category": "agronomic",
                        "priority": rule["severity"],
                        "confidence": 0.9,
                        "recommendation_az": rule["warning_az"],
                    }
                )
                additional_warnings.append(rule["warning_az"])
        except Exception:
            pass

    # If we have warnings, append them to the response
    current_response = state.get("current_response", "")

    if additional_warnings and current_response:
        warnings_text = "\n\n---\n**⚠️ Vacib Xəbərdarlıqlar:**\n" + "\n".join(additional_warnings)
        current_response = current_response + warnings_text

        logger.info(
            "validator_node_complete",
            matched_rules_count=len(matched_rules),
            warnings_added=len(additional_warnings),
        )

        return {
            "matched_rules": matched_rules,
            "current_response": current_response,
            "nodes_visited": nodes_visited,
        }

    logger.info(
        "validator_node_complete",
        matched_rules_count=len(matched_rules),
        warnings_added=0,
    )

    return {
        "matched_rules": matched_rules,
        "nodes_visited": nodes_visited,
    }


# ============================================================
# Pre-Response Validation (Quick checks)
# ============================================================


def quick_validate(state: AgentState) -> list[str]:
    """Quick validation before response generation.

    Returns list of critical warnings that should be shown immediately.
    Called by supervisor for fast feedback.
    """
    warnings = []

    weather = state.get("weather")
    if weather:
        if weather.temperature_c is not None and weather.temperature_c < -5:
            warnings.append("Şaxta xəbərdarlığı aktiv")
        if weather.temperature_c is not None and weather.temperature_c > 40:
            warnings.append("İstiliyk xəbərdarlığı aktiv")

    alerts = state.get("alerts", [])
    for alert in alerts:
        if alert.get("severity") in ["high", "critical"]:
            warnings.append(alert.get("message_az", "Xəbərdarlıq"))

    return warnings
