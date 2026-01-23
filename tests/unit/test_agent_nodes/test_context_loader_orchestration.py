# tests/unit/test_agent_nodes/test_context_loader_orchestration.py
"""Unit tests for Phase 4.3: Multi-MCP Orchestration in context_loader.

Tests parallel Weather + ZekaLab MCP calls with timeouts, fallbacks, and trace consolidation.
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from yonca.agent.nodes.context_loader import (
    _fetch_weather_mcp,
    _fetch_zekalab_rules_mcp,
    _noop_task,
    context_loader_node,
)
from yonca.agent.state import (
    AgentState,
    FarmContext,
    MCPTrace,
    RoutingDecision,
    UserIntent,
    WeatherContext,
)
from yonca.mcp.client import MCPClient

# ============================================================
# Helper Function Tests
# ============================================================


@pytest.mark.asyncio
async def test_fetch_weather_mcp_success():
    """Test successful weather MCP fetch."""
    with patch("yonca.mcp.handlers.get_weather_handler") as mock_get_handler:
        mock_handler = AsyncMock()
        mock_handler.get_forecast = AsyncMock(
            return_value=(
                {"current": {"temperature": 25.5}},
                MCPTrace(
                    server="openweather",
                    tool="get_forecast",
                    input_args={},
                    output={},
                    duration_ms=100.0,
                    success=True,
                ),
            )
        )
        mock_get_handler.return_value = mock_handler

        weather_data, trace = await _fetch_weather_mcp("farm_001", 40.4, 49.9)

        assert "current" in weather_data
        assert trace.server == "openweather"
        assert trace.success is True


@pytest.mark.asyncio
async def test_fetch_weather_mcp_failure():
    """Test weather MCP fetch with exception."""
    with patch("yonca.mcp.handlers.get_weather_handler") as mock_get_handler:
        mock_handler = AsyncMock()
        mock_handler.get_forecast = AsyncMock(side_effect=Exception("Network error"))
        mock_get_handler.return_value = mock_handler

        weather_data, trace = await _fetch_weather_mcp("farm_001", 40.4, 49.9)

        assert weather_data == {}
        assert trace.success is False
        assert "Network error" in trace.error_message


@pytest.mark.asyncio
async def test_fetch_zekalab_rules_mcp_success():
    """Test successful ZekaLab rules fetch."""
    with patch("yonca.mcp.handlers.get_zekalab_handler") as mock_get_handler:
        mock_handler = AsyncMock()
        mock_handler.get_rules_resource = AsyncMock(
            return_value=(
                {"rules": {"irrigation": {}, "fertilization": {}}},
                MCPTrace(
                    server="zekalab",
                    tool="get_rules",
                    input_args={},
                    output={"rules": {}},
                    duration_ms=150.0,
                    success=True,
                ),
            )
        )
        mock_get_handler.return_value = mock_handler

        rules_data, trace = await _fetch_zekalab_rules_mcp("farm_001", "wheat")

        assert "rules" in rules_data
        assert trace.server == "zekalab"
        assert trace.success is True


@pytest.mark.asyncio
async def test_fetch_zekalab_rules_mcp_failure():
    """Test ZekaLab rules fetch with exception."""
    with patch("yonca.mcp.handlers.get_zekalab_handler") as mock_get_handler:
        mock_handler = AsyncMock()
        mock_handler.get_rules_resource = AsyncMock(side_effect=Exception("API error"))
        mock_get_handler.return_value = mock_handler

        rules_data, trace = await _fetch_zekalab_rules_mcp("farm_001", "wheat")

        assert rules_data == {}
        assert trace.success is False
        assert "API error" in trace.error_message


@pytest.mark.asyncio
async def test_noop_task():
    """Test no-op task used for missing MCP servers."""
    result, trace = await _noop_task("test_server", "test_tool", {"arg": "value"})

    assert result == {}
    assert trace.server == "test_server"
    assert trace.tool == "test_tool"
    assert trace.success is False
    assert "No-op" in trace.error_message


# ============================================================
# Integration Tests - Context Loader Orchestration
# ============================================================


@pytest.mark.asyncio
async def test_context_loader_parallel_mcp_calls():
    """Test that context_loader makes parallel MCP calls."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
        data_consent_given=True,
    )

    with patch("yonca.agent.nodes.context_loader.get_db_session") as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        with patch("yonca.agent.nodes.context_loader.FarmRepository") as mock_farm_repo_class:
            mock_farm_repo = AsyncMock()
            mock_farm_repo_class.return_value = mock_farm_repo

            mock_farm = AsyncMock()
            mock_farm.farm_id = "farm_001"
            mock_farm_repo.get_primary_farm.return_value = mock_farm
            mock_farm_repo.get_context_for_ai.return_value = {
                "farm_id": "farm_001",
                "region": "aran",
                "crops": ["wheat"],
                "center_coordinates": {"latitude": 40.4, "longitude": 49.9},
            }

            with patch(
                "yonca.agent.nodes.context_loader._fetch_weather_mcp"
            ) as mock_weather, patch(
                "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
            ) as mock_zekalab:
                mock_weather.return_value = (
                    {"current": {"temperature": 25.5}},
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
                assert any(t["server"] == "openweather" for t in updates["mcp_traces"])
                assert any(t["server"] == "zekalab" for t in updates["mcp_traces"])


@pytest.mark.asyncio
async def test_context_loader_timeout_handling():
    """Test timeout handling for slow MCP servers."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
        data_consent_given=True,
    )

    async def slow_weather_call(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate slow server
        return {}, MCPTrace(server="openweather", tool="get_forecast", success=True)

    with patch("yonca.agent.nodes.context_loader.get_db_session"), patch(
        "yonca.agent.nodes.context_loader._fetch_weather_mcp", side_effect=slow_weather_call
    ), patch("yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp") as mock_zekalab:
        mock_zekalab.return_value = (
            {"rules": {}},
            MCPTrace(server="zekalab", tool="get_rules", success=True),
        )

        updates = await context_loader_node(state)

        # Should have fallback weather and ZekaLab trace
        assert "weather" in updates
        assert len(updates.get("mcp_traces", [])) > 0


@pytest.mark.asyncio
async def test_context_loader_partial_mcp_failure():
    """Test orchestration when one MCP server fails."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
        data_consent_given=True,
    )

    with patch("yonca.agent.nodes.context_loader.get_db_session"), patch(
        "yonca.agent.nodes.context_loader._fetch_weather_mcp"
    ) as mock_weather, patch(
        "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
    ) as mock_zekalab:
        # Weather succeeds
        mock_weather.return_value = (
            {"current": {"temperature": 25.5}},
            MCPTrace(server="openweather", tool="get_forecast", success=True),
        )

        # ZekaLab fails
        mock_zekalab.return_value = (
            {},
            MCPTrace(server="zekalab", tool="get_rules", success=False, error_message="API error"),
        )

        updates = await context_loader_node(state)

        # Should have weather but no rules
        assert "weather" in updates
        assert len(updates.get("mcp_traces", [])) == 2
        assert any(t["success"] is True for t in updates["mcp_traces"])
        assert any(t["success"] is False for t in updates["mcp_traces"])


@pytest.mark.asyncio
async def test_context_loader_mcp_disabled():
    """Test context loader with MCP disabled (uses synthetic fallback)."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": False, "fallback_to_synthetic": True},
        data_consent_given=True,
    )

    with patch("yonca.agent.nodes.context_loader.get_db_session"), patch(
        "yonca.agent.nodes.context_loader._get_synthetic_weather"
    ) as mock_synthetic:
        mock_synthetic.return_value = WeatherContext(
            temperature_c=20.0,
            humidity_percent=50.0,
            precipitation_mm=0.0,
            wind_speed_kmh=5.0,
            forecast_summary="Synthetic weather",
            last_updated=datetime.now(UTC),
        )

        updates = await context_loader_node(state)

        assert "weather" in updates
        assert updates["weather"].temperature_c == 20.0
        # No MCP traces since MCP disabled
        assert len(updates.get("mcp_traces", [])) == 0


@pytest.mark.asyncio
async def test_context_loader_no_consent():
    """Test context loader without data consent (no MCP calls)."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
        data_consent_given=False,  # No consent
    )

    with patch("yonca.agent.nodes.context_loader.get_db_session"), patch(
        "yonca.agent.nodes.context_loader._get_synthetic_weather"
    ) as mock_synthetic:
        mock_synthetic.return_value = WeatherContext(
            temperature_c=20.0,
            humidity_percent=50.0,
            precipitation_mm=0.0,
            wind_speed_kmh=5.0,
            forecast_summary="Synthetic weather",
            last_updated=datetime.now(UTC),
        )

        updates = await context_loader_node(state)

        assert "weather" in updates
        # Should use synthetic fallback
        assert len(updates.get("mcp_traces", [])) == 0


@pytest.mark.asyncio
async def test_mcp_trace_consolidation():
    """Test that MCP traces from multiple servers are properly consolidated."""
    state = AgentState(
        messages=[],
        user_id="user_001",
        intent=UserIntent.IRRIGATION,
        routing=RoutingDecision(
            target_node="context_loader",
            intent=UserIntent.IRRIGATION,
            confidence=0.9,
            requires_context=["weather"],
        ),
        farm_context=FarmContext(
            farm_id="farm_001",
            farm_name="Test Farm",
            region="aran",
            active_crops=["wheat"],
        ),
        mcp_config={"use_mcp": True, "fallback_to_synthetic": True},
        data_consent_given=True,
        mcp_traces=[
            # Existing trace from earlier node
            {
                "server": "previous",
                "tool": "old_tool",
                "input_args": {},
                "output": {},
                "duration_ms": 100,
                "success": True,
            }
        ],
    )

    with patch("yonca.agent.nodes.context_loader.get_db_session"), patch(
        "yonca.agent.nodes.context_loader._fetch_weather_mcp"
    ) as mock_weather, patch(
        "yonca.agent.nodes.context_loader._fetch_zekalab_rules_mcp"
    ) as mock_zekalab:
        mock_weather.return_value = (
            {"current": {}},
            MCPTrace(server="openweather", tool="get_forecast", success=True),
        )

        mock_zekalab.return_value = (
            {"rules": {}},
            MCPTrace(server="zekalab", tool="get_rules", success=True),
        )

        updates = await context_loader_node(state)

        # Should have 3 traces total (1 existing + 2 new)
        assert len(updates.get("mcp_traces", [])) == 3
        assert any(t["server"] == "previous" for t in updates["mcp_traces"])
        assert any(t["server"] == "openweather" for t in updates["mcp_traces"])
        assert any(t["server"] == "zekalab" for t in updates["mcp_traces"])


async def test_make_request_basic_auth():
    """Test request with basic authentication."""
    async with httpx.AsyncClient() as http_client:
        client = MCPClient(
            server_name="test",
            base_url="http://test.local",
            http_client=http_client,
            auth={
                "type": "basic",
                "username": "user",  # pragma: allowlist secret
                "password": "pass123",  # pragma: allowlist secret
            },
        )

        with respx.mock:
            respx.get("http://test.local/data").mock(
                return_value=httpx.Response(200, json={"data": "test"})
            )

            response = await client.make_request("GET", "/data")
            assert response == {"data": "test"}


async def test_make_request_bearer_auth():
    """Test request with bearer token authentication."""
    async with httpx.AsyncClient() as http_client:
        client = MCPClient(
            server_name="test",
            base_url="http://test.local",
            http_client=http_client,
            auth={"type": "bearer", "token": "secret_token_xyz"},  # pragma: allowlist secret
        )

        with respx.mock:
            respx.get("http://test.local/data").mock(
                return_value=httpx.Response(200, json={"data": "test"})
            )

            response = await client.make_request("GET", "/data")
            assert response == {"data": "test"}
