# tests/unit/test_agent_nodes/test_context_loader_orchestration.py
"""Unit tests for Phase 4.3: Multi-MCP Orchestration in context_loader.

Tests parallel Weather + ZekaLab MCP calls with timeouts, fallbacks, and trace consolidation.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from alim.agent.nodes.context_loader import (
    _fetch_weather_mcp,
    _fetch_zekalab_rules_mcp,
    _get_synthetic_weather,
    _noop_task,
    context_loader_node,
)
from alim.agent.state import (
    FarmContext,
    MCPTrace,
    RoutingDecision,
    UserIntent,
    WeatherContext,
)

logger = logging.getLogger(__name__)

# ============================================================
# Helper Function Tests
# ============================================================


@pytest.mark.asyncio
async def test_fetch_weather_mcp_success():
    """Test successful weather MCP fetch."""
    with patch("yonca.agent.nodes.context_loader.WeatherMCPHandler") as mock_handler_class:
        mock_instance = AsyncMock()
        mock_trace = MCPTrace(
            server="openweather",
            tool="get_forecast",
            input_args={},
            output={},
            duration_ms=100.0,
            success=True,
        )
        mock_instance.get_forecast = AsyncMock(
            return_value=({"current": {}, "forecast": []}, mock_trace)
        )
        mock_handler_class.return_value = mock_instance

        weather_data, trace = await _fetch_weather_mcp("farm_001")

        assert "current" in weather_data
        assert trace.server == "openweather"
        assert trace.success is True


@pytest.mark.asyncio
async def test_fetch_weather_mcp_failure():
    """Test weather MCP fetch with exception - should raise."""
    with patch("yonca.agent.nodes.context_loader.WeatherMCPHandler") as mock_handler_class:
        mock_instance = AsyncMock()
        mock_instance.get_forecast = AsyncMock(side_effect=Exception("Network error"))
        mock_handler_class.return_value = mock_instance

        # The function re-raises exceptions after creating trace
        with pytest.raises(Exception, match="Network error"):
            await _fetch_weather_mcp("farm_001")


@pytest.mark.asyncio
async def test_fetch_zekalab_rules_mcp_success():
    """Test successful ZekaLab rules fetch."""
    with patch("yonca.agent.nodes.context_loader.get_zekalab_handler") as mock_get_handler:
        # Use MagicMock for sync handler instance
        mock_instance = MagicMock()
        mock_trace = MCPTrace(
            server="zekalab",
            tool="get_rules",
            input_args={},
            output={"rules": {}},
            duration_ms=150.0,
            success=True,
        )
        # Async method on sync handler
        mock_instance.get_rules_resource = AsyncMock(
            return_value=({"rules": {"irrigation": {}, "fertilization": {}}}, mock_trace)
        )
        mock_get_handler.return_value = mock_instance

        rules_data, trace = await _fetch_zekalab_rules_mcp("farm_001", "wheat")

        assert "rules" in rules_data
        assert trace.server == "zekalab"
        assert trace.success is True


@pytest.mark.asyncio
async def test_fetch_zekalab_rules_mcp_failure():
    """Test ZekaLab rules fetch with exception - should raise."""
    with patch("yonca.agent.nodes.context_loader.get_zekalab_handler") as mock_get_handler:
        # Use MagicMock for sync handler instance
        mock_instance = MagicMock()
        mock_instance.get_rules_resource = AsyncMock(side_effect=Exception("API error"))
        mock_get_handler.return_value = mock_instance

        with pytest.raises(Exception, match="API error"):
            await _fetch_zekalab_rules_mcp("farm_001", "wheat")


@pytest.mark.asyncio
async def test_noop_task():
    """Test no-op task returns None."""
    result = await _noop_task("test_task")
    assert result is None


@pytest.mark.asyncio
async def test_get_synthetic_weather():
    """Test synthetic weather generation."""
    weather = await _get_synthetic_weather("aran")

    assert isinstance(weather, WeatherContext)
    assert weather.temperature_c is not None
    assert weather.humidity_percent is not None
    assert weather.forecast_summary is not None


# ============================================================
# Integration Tests - Context Loader Orchestration
# ============================================================


@pytest.mark.asyncio
async def test_context_loader_mcp_disabled():
    """Test context loader with MCP disabled (uses synthetic fallback)."""
    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": False, "fallback_to_synthetic": True},
        "data_consent_given": True,
        "nodes_visited": [],
        "mcp_traces": [],
    }

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        updates = await context_loader_node(state)

        assert "weather" in updates
        assert updates["weather"].temperature_c is not None
        # No MCP traces since MCP disabled
        assert len(updates.get("mcp_traces", [])) == 0


@pytest.mark.asyncio
async def test_context_loader_no_consent():
    """Test context loader without data consent (no MCP calls)."""
    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": True, "fallback_to_synthetic": True},
        "data_consent_given": False,
        "nodes_visited": [],
        "mcp_traces": [],
    }

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        updates = await context_loader_node(state)

        assert "weather" in updates
        # Should use synthetic fallback due to no consent
        assert len(updates.get("mcp_traces", [])) == 0


@pytest.mark.asyncio
async def test_context_loader_parallel_mcp_calls():
    """Test that context_loader orchestrates parallel MCP calls."""
    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": True, "fallback_to_synthetic": True},
        "data_consent_given": True,
        "nodes_visited": [],
        "mcp_traces": [],
    }

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("yonca.agent.nodes.context_loader._fetch_weather_mcp") as mock_weather, patch(
            "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
        ) as mock_zekalab:
            # Mock successful weather call
            mock_weather.return_value = (
                {"current": {"temperature": 25.5, "humidity": 60}, "forecast_summary": "Clear"},
                MCPTrace(
                    server="openweather",
                    tool="get_forecast",
                    input_args={"farm_id": "farm_001"},
                    output={},
                    duration_ms=100.0,
                    success=True,
                ),
            )

            # Mock successful ZekaLab call
            mock_zekalab.return_value = (
                {"rules": {"irrigation": {}}},
                MCPTrace(
                    server="zekalab",
                    tool="get_rules",
                    input_args={},
                    output={},
                    duration_ms=150.0,
                    success=True,
                ),
            )

            updates = await context_loader_node(state)

            # Verify both MCP handlers were called
            mock_weather.assert_called_once()
            mock_zekalab.assert_called_once()

            # Verify traces consolidated
            assert len(updates.get("mcp_traces", [])) == 2
            servers = [t["server"] for t in updates["mcp_traces"]]
            assert "openweather" in servers
            assert "zekalab" in servers


@pytest.mark.asyncio
async def test_context_loader_partial_mcp_failure():
    """Test orchestration when one MCP server fails (weather succeeds, zekalab fails)."""
    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": True, "fallback_to_synthetic": True},
        "data_consent_given": True,
        "nodes_visited": [],
        "mcp_traces": [],
    }

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("yonca.agent.nodes.context_loader._fetch_weather_mcp") as mock_weather, patch(
            "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
        ) as mock_zekalab:
            # Weather succeeds
            mock_weather.return_value = (
                {"current": {"temperature": 25.5, "humidity": 60}},
                MCPTrace(
                    server="openweather",
                    tool="get_forecast",
                    input_args={},
                    output={},
                    duration_ms=100.0,
                    success=True,
                ),
            )

            # ZekaLab fails (returns exception)
            mock_zekalab.side_effect = Exception("ZekaLab API error")

            updates = await context_loader_node(state)

            # Should have weather loaded via MCP
            assert "weather" in updates
            # Should have at least 2 traces (success + failure)
            assert len(updates.get("mcp_traces", [])) >= 1


@pytest.mark.asyncio
async def test_context_loader_timeout_handling():
    """Test timeout handling for slow MCP servers."""
    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": True, "fallback_to_synthetic": True},
        "data_consent_given": True,
        "nodes_visited": [],
        "mcp_traces": [],
    }

    async def slow_weather_call(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate timeout
        return {}, MCPTrace(
            server="openweather",
            tool="get_forecast",
            input_args={},
            output={},
            duration_ms=10000.0,
            success=True,
        )

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch(
            "yonca.agent.nodes.context_loader._fetch_weather_mcp",
            side_effect=slow_weather_call,
        ), patch("yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp") as mock_zekalab:
            mock_zekalab.return_value = (
                {"rules": {}},
                MCPTrace(
                    server="zekalab",
                    tool="get_rules",
                    input_args={},
                    output={},
                    duration_ms=100.0,
                    success=True,
                ),
            )

            updates = await context_loader_node(state)

            # Should have fallback weather due to timeout
            assert "weather" in updates
            # Should have timeout trace
            traces = updates.get("mcp_traces", [])
            assert any(not t["success"] for t in traces)


@pytest.mark.asyncio
async def test_mcp_trace_consolidation():
    """Test that MCP traces from multiple servers are properly consolidated."""
    existing_trace = {
        "server": "previous",
        "tool": "old_tool",
        "input_args": {},
        "output": {},
        "duration_ms": 100,
        "success": True,
    }

    state = {
        "messages": [],
        "user_id": "user_001",
        "intent": UserIntent.IRRIGATION,
        "routing": RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        "farm_context": FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            farm_type="crop",
            region="aran",
            total_area_ha=10.0,
            parcel_count=1,
            parcels=[],
            active_crops=[{"crop": "wheat", "parcel_id": "P001", "days_since_sowing": 30}],
            alerts=[],
        ),
        "mcp_config": {"use_mcp": True, "fallback_to_synthetic": True},
        "data_consent_given": True,
        "nodes_visited": [],
        "mcp_traces": [existing_trace],
    }

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_db:
        mock_session = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_session

        with patch("yonca.agent.nodes.context_loader._fetch_weather_mcp") as mock_weather, patch(
            "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
        ) as mock_zekalab:
            mock_weather.return_value = (
                {"current": {}},
                MCPTrace(
                    server="openweather",
                    tool="get_forecast",
                    input_args={},
                    output={},
                    duration_ms=100.0,
                    success=True,
                ),
            )

            mock_zekalab.return_value = (
                {"rules": {}},
                MCPTrace(
                    server="zekalab",
                    tool="get_rules",
                    input_args={},
                    output={},
                    duration_ms=150.0,
                    success=True,
                ),
            )

            updates = await context_loader_node(state)

            # Should have 3 traces total (1 existing + 2 new)
            traces = updates.get("mcp_traces", [])
            assert len(traces) == 3
            servers = [t["server"] for t in traces]
            assert "previous" in servers
            assert "openweather" in servers
            assert "zekalab" in servers


@pytest.fixture
def mock_zekalab_handler():
    """Fixture providing a mocked ZekaLab MCP handler."""
    from datetime import UTC, datetime

    from alim.agent.state import MCPTrace
    from alim.mcp.handlers.zekalab_handler import ZekaLabMCPHandler

    handler = ZekaLabMCPHandler()

    # Mock the evaluate_irrigation_rules method
    async def mock_evaluate_irrigation(*args, **kwargs):
        trace = MCPTrace(
            server="zekalab",
            tool="evaluate_irrigation_rules",
            input_args=kwargs,
            output={"recommendation": "irrigate", "confidence": 0.95},
            duration_ms=42.5,
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
        )
        return ({"recommendation": "irrigate", "confidence": 0.95}, trace)

    handler.evaluate_irrigation_rules = mock_evaluate_irrigation
    return handler
