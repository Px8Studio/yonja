"""
Yonca AI - LangGraph Agent
AI-powered farm assistant using LangGraph orchestration.
"""
from yonca.agent.graph import (
    YoncaAgent,
    create_yonca_agent,
    create_gemini_agent,
    create_ollama_agent,
    AgentState,
)
from yonca.agent.tools import (
    ALL_TOOLS,
    get_weather_tool,
    get_soil_analysis_tool,
    get_irrigation_recommendation_tool,
    get_fertilization_recommendation_tool,
    get_pest_alert_tool,
    get_harvest_timing_tool,
    get_livestock_health_tool,
    get_daily_schedule_tool,
)

__all__ = [
    # Main Agent
    "YoncaAgent",
    "create_yonca_agent",
    "AgentState",
    # Provider-specific factories
    "create_gemini_agent",
    "create_ollama_agent",
    # Tools
    "ALL_TOOLS",
    "get_weather_tool",
    "get_soil_analysis_tool",
    "get_irrigation_recommendation_tool",
    "get_fertilization_recommendation_tool",
    "get_pest_alert_tool",
    "get_harvest_timing_tool",
    "get_livestock_health_tool",
    "get_daily_schedule_tool",
]
