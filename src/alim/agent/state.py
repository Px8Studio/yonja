# src/ALİM/agent/state.py
"""LangGraph state schema for the ALİM agent.

Defines the typed state that flows through the agent graph,
including conversation history, farm context, and routing decisions.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

# ============================================================
# MCP (Model Context Protocol) Types - Phase 2
# ============================================================


class MCPTrace(BaseModel):
    """Record of a single MCP tool call for audit trail."""

    server: str  # "openweather", "zekalab", etc.
    tool: str  # "get_forecast", "evaluate_irrigation_rules", etc.
    input_args: dict  # Arguments passed to tool
    output: dict  # Result from tool
    duration_ms: float  # How long the call took
    success: bool  # Did it succeed?
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================
# Intent Classification
# ============================================================


class UserIntent(str, Enum):
    """Classified intent of the user's message.

    The supervisor node classifies each message into one of these intents
    to route to the appropriate specialist node.
    """

    # Farming advice intents
    IRRIGATION = "irrigation"  # Suvarma - watering questions
    FERTILIZATION = "fertilization"  # Gübrələmə - fertilizer questions
    PEST_CONTROL = "pest_control"  # Zərərverici - pest/disease questions
    HARVEST = "harvest"  # Məhsul yığımı - harvest timing
    PLANTING = "planting"  # Əkin - planting/sowing questions
    CROP_ROTATION = "crop_rotation"  # Növbəli əkin - rotation planning

    # Weather-related
    WEATHER = "weather"  # Hava - weather questions

    # General
    GREETING = "greeting"  # Salam - greetings
    GENERAL_ADVICE = "general_advice"  # Ümumi - general farming advice
    OFF_TOPIC = "off_topic"  # Mövzudan kənar

    # Clarification
    CLARIFICATION = "clarification"  # Dəqiqləşdirmə - need more info

    # Data query (NL → SQL)
    DATA_QUERY = "data_query"  # Verilənlər bazası sorğuları / NL-to-SQL

    # Vision analysis (image → action)
    VISION_ANALYSIS = "vision_analysis"  # Şəkil analizi / təsir təklifi


class Severity(str, Enum):
    """Severity level for alerts and recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# Message Types
# ============================================================


class Message(BaseModel):
    """A single message in the conversation.

    Includes metadata for observability and audit trails.
    """

    model_config = {"use_enum_values": True}

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Metadata
    intent: UserIntent | None = None
    confidence: float | None = None
    node_source: str | None = None  # Which node generated this


class Alert(BaseModel):
    """An alert requiring user attention.

    Generated from NDVI readings, weather, or rule engine.
    """

    alert_type: str
    parcel_id: str | None = None
    severity: Severity = Severity.MEDIUM
    message_az: str
    message_en: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================
# Context Types
# ============================================================


class UserContext(BaseModel):
    """User profile context for personalization.

    Loaded from database via UserRepository.get_context_for_ai()
    """

    user_id: str
    display_name: str
    experience_level: str  # "novice", "intermediate", "expert"
    preferred_language: str = "az"
    farm_count: int = 0
    total_area_ha: float = 0.0
    primary_activities: list[str] = Field(default_factory=list)


class FarmContext(BaseModel):
    """Farm context for recommendations.

    Loaded from database via FarmRepository.get_context_for_ai()
    """

    farm_id: str
    farm_name: str
    farm_type: str
    region: str
    total_area_ha: float
    parcel_count: int = 0
    parcels: list[dict] = Field(default_factory=list)
    active_crops: list[dict] = Field(default_factory=list)
    alerts: list[dict] = Field(default_factory=list)
    center_coordinates: dict | None = None


class ScenarioContext(BaseModel):
    """Dynamic farm scenario context from chat settings.

    Tracks evolving user configuration during conversation.
    Enables rules engine to generate contextual monthly plans.
    """

    scenario_id: str | None = None  # UUID from farm_scenario_plans table
    crop_category: str | None = None  # Danli, Taravaz, Texniki, Yem, Meyva
    specific_crop: str  # Pambiq, Bugda, Kalam, etc.
    region: str  # Aran, Quba-Xacmaz, etc.
    farm_size_ha: float  # Farm size in hectares
    experience_level: str  # novice, intermediate, expert
    soil_type: str  # Gilli/Clay, Qumlu/Sandy, Lopam/Loam, Soranli/Saline
    irrigation_type: str  # Damci/Drip, Pivot, Sirim/Flood, Yagis/Rainfed
    current_month: str  # January-December
    action_categories: list[str] = Field(default_factory=list)  # ['Ekin', 'Suvarma', etc.]
    expertise_areas: list[str] = Field(default_factory=list)  # ['cotton', 'wheat', etc.]
    conversation_stage: str = "profile_setup"  # profile_setup, planning_active, plan_confirmed
    settings_version: int = 1  # Increments on each settings update


class WeatherContext(BaseModel):
    """Weather data for recommendations.

    Will be populated from weather API or synthetic data.
    """

    temperature_c: float | None = None
    humidity_percent: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    forecast_summary: str | None = None
    last_updated: datetime | None = None


# ============================================================
# Routing State
# ============================================================


class RoutingDecision(BaseModel):
    """Supervisor's routing decision.

    Determines which specialist node handles the request.
    """

    target_node: str  # "agronomist", "weather", "validator", "end"
    intent: UserIntent
    confidence: float
    reasoning: str | None = None
    requires_context: list[str] = Field(default_factory=list)  # ["farm", "weather", "user"]


# ============================================================
# Rule Engine Results
# ============================================================


class RuleMatch(BaseModel):
    """A matched rule from the agronomy rules engine."""

    rule_id: str
    rule_name: str
    category: str  # "irrigation", "fertilization", etc.
    priority: str  # "low", "medium", "high", "critical"
    confidence: float
    recommendation_az: str
    recommendation_en: str | None = None
    data: dict = Field(default_factory=dict)


# ============================================================
# Main Agent State (TypedDict for LangGraph)
# ============================================================


def _merge_alerts(
    existing: list[dict],
    new: list[dict],
) -> list[dict]:
    """Reducer function to merge alert lists, avoiding duplicates."""
    existing_ids = {(a.get("alert_type"), a.get("parcel_id")) for a in existing}
    unique_new = [a for a in new if (a.get("alert_type"), a.get("parcel_id")) not in existing_ids]
    return existing + unique_new


def _merge_rules(
    existing: list[dict],
    new: list[dict],
) -> list[dict]:
    """Reducer function to merge matched rules."""
    existing_ids = {r.get("rule_id") for r in existing}
    unique_new = [r for r in new if r.get("rule_id") not in existing_ids]
    return existing + unique_new


class AgentState(TypedDict, total=False):
    """Main state that flows through the LangGraph agent.

    This TypedDict defines all state that can be accessed and modified
    by agent nodes. Uses LangGraph's Annotated type for reducers.

    State Flow:
    1. User sends message -> messages updated
    2. Supervisor classifies intent -> routing set
    3. Context loaded if needed -> user_context, farm_context, weather
    4. Specialist processes -> generates response
    5. Validator checks rules -> matched_rules populated
    6. Response sent -> messages updated with assistant reply

    Thread-Based Memory:
    - Each conversation has a unique thread_id
    scenario_context: ScenarioContext | None  # Dynamic chat settings scenario
    - State is checkpointed to Redis after each step
    - Farmer can resume conversation even after app close
    """

    # ===== Session Identity =====
    thread_id: str  # Unique conversation ID
    user_id: str | None  # Authenticated user ID (if available)
    session_id: str | None  # Session ID from API

    # ===== Conversation =====
    messages: Annotated[list, add_messages]  # Full conversation history (HumanMessage/AIMessage)
    current_input: str  # Latest user input
    current_response: str | None  # Generated response (before sending)

    # ===== Intent & Routing =====
    routing: RoutingDecision | None  # Supervisor's routing decision
    intent: UserIntent | None  # Classified intent
    intent_confidence: float  # Intent classification confidence

    # ===== Context (Loaded on Demand) =====
    user_context: UserContext | None  # User profile
    farm_context: FarmContext | None  # Active farm data
    scenario_context: ScenarioContext | None  # Dynamic chat settings scenario
    weather: WeatherContext | None  # Current weather

    # ===== Rule Engine =====
    matched_rules: Annotated[list[dict], _merge_rules]  # Matched agronomy rules

    # ===== Alerts =====
    alerts: Annotated[list[dict], _merge_alerts]  # Active alerts

    # ===== Processing Metadata =====
    processing_start: datetime | None  # When processing started
    nodes_visited: list[str]  # Audit trail of nodes

    # ===== Error Handling =====
    error: str | None  # Error message if any
    error_node: str | None  # Node where error occurred
    retry_count: int  # Number of retries attempted
    last_error_timestamp: datetime | None  # When last error occurred

    # ===== Output Control =====
    should_stream: bool  # Whether to stream response
    language: str  # Response language (default: "az")

    # ===== MCP Orchestration (Phase 2) =====
    mcp_traces: Annotated[list[dict], _merge_rules]  # All MCP calls made during this turn
    data_consent_given: bool  # User consented to use external APIs
    mcp_server_health: dict[str, bool]  # Health status of each MCP server
    mcp_config: dict  # Session-level MCP configuration

    # ===== Document Processing (Phase 3) =====
    file_paths: list[str]  # Uploaded file paths for document processing

    # ===== Versioning (Phase 4) =====
    version: int  # Schema version for migrations


# ============================================================
# State Helpers
# ============================================================


def create_initial_state(
    thread_id: str,
    user_input: str,
    user_id: str | None = None,
    session_id: str | None = None,
    language: str = "az",
    system_prompt_override: str | None = None,
    scenario_context: dict | None = None,
    data_consent_given: bool = False,
    file_paths: list[str] | None = None,
) -> AgentState:
    """Create initial state for a new conversation turn.

    DEPRECATED: Use setup_node() in the graph instead.
    This function is kept for backward compatibility with tests.

    Args:
        thread_id: Unique conversation identifier
        user_input: The user's message
        user_id: Authenticated user ID (optional)
        session_id: API session ID (optional)
        language: Response language (default Azerbaijani)
        system_prompt_override: Custom system prompt for profile-specific behavior (optional)
        scenario_context: Farm scenario from chat settings (optional)
        data_consent_given: Whether user consented to use external APIs (optional)
        file_paths: Uploaded file paths for document processing (optional)

    Returns:
        Initialized AgentState ready for graph execution.
    """
    # Build initial human message
    human_msg = HumanMessage(content=user_input)

    # If system prompt override provided, inject it as a system message
    messages = []
    if system_prompt_override:
        from langchain_core.messages import SystemMessage

        messages.append(SystemMessage(content=system_prompt_override))
    messages.append(human_msg)

    # Convert scenario_context dict to ScenarioContext if provided
    scenario_ctx = None
    if scenario_context:
        scenario_ctx = ScenarioContext(**scenario_context)

    return AgentState(
        thread_id=thread_id,
        user_id=user_id,
        session_id=session_id,
        messages=messages,
        current_input=user_input,
        current_response=None,
        routing=None,
        intent=None,
        intent_confidence=0.0,
        user_context=None,
        farm_context=None,
        scenario_context=scenario_ctx,
        weather=None,
        matched_rules=[],
        alerts=[],
        processing_start=datetime.now(UTC),
        nodes_visited=[],
        # Error Handling
        error=None,
        error_node=None,
        retry_count=0,
        last_error_timestamp=None,
        should_stream=False,
        language=language,
        # MCP Orchestration (Phase 2)
        mcp_traces=[],
        data_consent_given=data_consent_given,
        mcp_server_health={
            "openweather": True,
            "zekalab": True,
        },
        mcp_config={
            "use_mcp": True,
            "fallback_to_synthetic": True,
            "max_mcp_calls_per_turn": 10,
            "mcp_timeout_seconds": 5,
        },
        # Document Processing (Phase 3)
        file_paths=file_paths or [],
        # Versioning (Phase 4)
        version=1,
    )


def add_assistant_message(
    state: AgentState,  # noqa: ARG001 - kept for API compatibility
    content: str,
    node_source: str,
    intent: UserIntent | None = None,
) -> AIMessage:
    """Create an assistant message to add to state.

    Returns an AIMessage that will be merged by langgraph's add_messages reducer.
    Metadata is stored in the message's additional_kwargs.

    Args:
        state: Current agent state (unused, kept for API compatibility)
        content: Response text
        node_source: Which node generated this response
        intent: Detected user intent
    """
    return AIMessage(
        content=content,
        additional_kwargs={
            "timestamp": datetime.now(UTC).isoformat(),
            "node_source": node_source,
            "intent": intent.value if intent else None,
        },
    )


def serialize_state_for_api(state: AgentState) -> dict:
    """Serialize AgentState to a JSON-compatible dict for HTTP APIs.

    LangGraph Dev Server API requires plain dicts, not LangChain message objects.
    This helper converts SystemMessage/HumanMessage/AIMessage to plain dicts.

    Args:
        state: The AgentState TypedDict

    Returns:
        JSON-serializable dict suitable for LangGraph Dev Server API
    """
    from langchain_core.messages import SystemMessage

    result = dict(state)

    # Serialize messages to plain dicts
    if "messages" in result and result["messages"]:
        serialized_messages = []
        for msg in result["messages"]:
            if isinstance(msg, SystemMessage):
                serialized_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                serialized_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                serialized_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        **(
                            {"additional_kwargs": msg.additional_kwargs}
                            if msg.additional_kwargs
                            else {}
                        ),
                    }
                )
            elif isinstance(msg, dict):
                # Already a dict, pass through
                serialized_messages.append(msg)
            else:
                # Unknown type, try to convert
                serialized_messages.append({"role": "unknown", "content": str(msg)})
        result["messages"] = serialized_messages

    # Serialize Pydantic models to dicts
    for key in ["routing", "user_context", "farm_context", "scenario_context", "weather"]:
        if key in result and result[key] is not None:
            if hasattr(result[key], "model_dump"):
                result[key] = result[key].model_dump()

    # Convert datetime to ISO string
    if "processing_start" in result and result["processing_start"]:
        result["processing_start"] = result["processing_start"].isoformat()

    return result


def get_conversation_summary(state: AgentState, max_messages: int = 10) -> str:
    """Get a summary of recent conversation for context.

    Useful for providing context to LLM without overwhelming token limit.
    """
    messages = state.get("messages", [])[-max_messages:]

    lines = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            role = "unknown"
        content = (msg.content if isinstance(msg, BaseMessage) else str(msg))[:200]
        lines.append(f"{role}: {content}")

    return "\n".join(lines)
