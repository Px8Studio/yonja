# tests/unit/test_agent_state.py
"""Unit tests for agent state management."""

from datetime import datetime

from alim.agent.state import (
    Alert,
    FarmContext,
    Message,
    RoutingDecision,
    Severity,
    UserContext,
    UserIntent,
    WeatherContext,
    add_assistant_message,
    create_initial_state,
    get_conversation_summary,
    setup_node,
)
from langchain_core.messages import AIMessage, HumanMessage


class TestUserIntent:
    """Tests for UserIntent enum."""

    def test_all_intents_defined(self):
        """Verify all expected intents are defined."""
        expected = [
            "irrigation",
            "fertilization",
            "pest_control",
            "harvest",
            "planting",
            "crop_rotation",
            "weather",
            "greeting",
            "general_advice",
            "off_topic",
            "clarification",
        ]

        for intent in expected:
            assert UserIntent(intent) is not None

    def test_intent_values(self):
        """Verify intent string values."""
        assert UserIntent.IRRIGATION.value == "irrigation"
        assert UserIntent.FERTILIZATION.value == "fertilization"
        assert UserIntent.WEATHER.value == "weather"
        assert UserIntent.GREETING.value == "greeting"


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_levels(self):
        """Verify severity levels."""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"


class TestMessage:
    """Tests for Message model."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Salam")

        assert msg.role == "user"
        assert msg.content == "Salam"
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_metadata(self):
        """Test message with optional fields."""
        msg = Message(
            role="assistant",
            content="Salam, sizə kömək edim",
            intent=UserIntent.GREETING,
            confidence=0.95,
            node_source="supervisor",
        )

        assert msg.intent == UserIntent.GREETING
        assert msg.confidence == 0.95
        assert msg.node_source == "supervisor"


class TestAlert:
    """Tests for Alert model."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            alert_type="ndvi_stress",
            parcel_id="AZ-ARN-1234",
            severity=Severity.HIGH,
            message_az="Bitki stressi aşkarlandı",
        )

        assert alert.alert_type == "ndvi_stress"
        assert alert.parcel_id == "AZ-ARN-1234"
        assert alert.severity == Severity.HIGH

    def test_alert_default_severity(self):
        """Test default severity is medium."""
        alert = Alert(
            alert_type="test",
            message_az="Test xəbərdarlıq",
        )

        assert alert.severity == Severity.MEDIUM


class TestUserContext:
    """Tests for UserContext model."""

    def test_user_context_creation(self):
        """Test creating user context."""
        ctx = UserContext(
            user_id="user_123",
            display_name="Əhməd",
            experience_level="intermediate",
            farm_count=2,
            total_area_ha=15.5,
        )

        assert ctx.user_id == "user_123"
        assert ctx.display_name == "Əhməd"
        assert ctx.experience_level == "intermediate"
        assert ctx.preferred_language == "az"  # default


class TestFarmContext:
    """Tests for FarmContext model."""

    def test_farm_context_creation(self):
        """Test creating farm context."""
        ctx = FarmContext(
            farm_id="farm_123",
            farm_name="Günəş Təsərrüfatı",
            farm_type="crop_production",
            region="aran",
            total_area_ha=25.0,
        )

        assert ctx.farm_id == "farm_123"
        assert ctx.farm_name == "Günəş Təsərrüfatı"
        assert ctx.parcel_count == 0  # default
        assert ctx.parcels == []  # default


class TestWeatherContext:
    """Tests for WeatherContext model."""

    def test_weather_context_creation(self):
        """Test creating weather context."""
        ctx = WeatherContext(
            temperature_c=25.5,
            humidity_percent=60.0,
            precipitation_mm=0.0,
            wind_speed_kmh=10.0,
            forecast_summary="Açıq hava",
        )

        assert ctx.temperature_c == 25.5
        assert ctx.humidity_percent == 60.0


class TestRoutingDecision:
    """Tests for RoutingDecision model."""

    def test_routing_decision_creation(self):
        """Test creating routing decision."""
        decision = RoutingDecision(
            target_node="agronomist",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            reasoning="Suvarma ilə bağlı sual",
            requires_context=["farm", "weather"],
        )

        assert decision.target_node == "agronomist"
        assert decision.intent == UserIntent.IRRIGATION
        assert "farm" in decision.requires_context


class TestCreateInitialState:
    """Tests for create_initial_state function."""

    def test_basic_state_creation(self):
        """Test creating basic initial state."""
        state = create_initial_state(
            thread_id="thread_123",
            user_input="Salam",
        )

        assert state["thread_id"] == "thread_123"
        assert state["current_input"] == "Salam"
        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "Salam"

    def test_state_with_user_id(self):
        """Test state with user context."""
        state = create_initial_state(
            thread_id="thread_123",
            user_input="Necəsən?",
            user_id="user_456",
            session_id="session_789",
        )

        assert state["user_id"] == "user_456"
        assert state["session_id"] == "session_789"

    def test_state_defaults(self):
        """Test default values in state."""
        state = create_initial_state(
            thread_id="thread_123",
            user_input="Test",
        )

        assert state["routing"] is None
        assert state["intent"] is None
        assert state["matched_rules"] == []
        assert state["alerts"] == []
        assert state["error"] is None
        assert state["language"] == "az"


class TestAddAssistantMessage:
    """Tests for add_assistant_message function."""

    def test_add_message(self):
        """Test adding assistant message."""
        state = create_initial_state("t1", "Test")

        msg = add_assistant_message(
            state,
            content="Salam, sizə kömək edim",
            node_source="agronomist",
            intent=UserIntent.GREETING,
        )

        assert isinstance(msg, AIMessage)
        assert msg.content == "Salam, sizə kömək edim"
        assert msg.additional_kwargs["node_source"] == "agronomist"
        assert msg.additional_kwargs["intent"] == "greeting"


class TestGetConversationSummary:
    """Tests for get_conversation_summary function."""

    def test_summary_with_messages(self):
        """Test getting conversation summary."""
        state = create_initial_state("t1", "Salam")
        state["messages"].append(AIMessage(content="Xoş gördük! Sizə necə kömək edə bilərəm?"))
        state["messages"].append(HumanMessage(content="Pomidor əkmək istəyirəm"))

        summary = get_conversation_summary(state)

        assert "Salam" in summary
        assert "Xoş gördük" in summary
        assert "Pomidor" in summary

    def test_summary_truncation(self):
        """Test message truncation in summary."""
        state = create_initial_state("t1", "x" * 500)  # Long message

        summary = get_conversation_summary(state)

        # Message should be truncated to 200 chars
        assert len(summary) < 500


class TestSetupNode:
    """Tests for setup_node function."""

    def test_setup_node_creates_messages(self):
        """Test creating messages from input."""
        state = {"current_input": "Salam"}
        updates = setup_node(state)

        assert "messages" in updates
        assert len(updates["messages"]) == 1
        assert updates["messages"][0].content == "Salam"
        assert "processing_start" in updates
        assert "nodes_visited" in updates

    def test_setup_node_preserves_existing(self):
        """Test preserving existing state."""
        existing_msgs = [HumanMessage(content="Old")]
        state = {"current_input": "New", "messages": existing_msgs, "nodes_visited": ["setup"]}
        updates = setup_node(state)

        # Should NOT overwrite messages if already present
        assert "messages" not in updates
        assert "nodes_visited" not in updates
        # processing_start missing, so it should add it
        assert "processing_start" in updates
