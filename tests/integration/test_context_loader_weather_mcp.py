"""Integration tests for Phase 2 - Weather MCP Integration."""

from unittest.mock import AsyncMock, patch

import pytest
from alim.agent.nodes.context_loader import context_loader_node
from alim.agent.state import (
    RoutingDecision,
    UserIntent,
    create_initial_state,
)


@pytest.fixture
def initial_state():
    """Create initial agent state."""
    return create_initial_state(
        thread_id="test_thread_123",
        user_input="Should I water my cotton?",
        user_id="user_456",
        data_consent_given=True,  # User consented to MCP
    )


@pytest.mark.asyncio
async def test_context_loader_calls_weather_mcp(initial_state):
    """Test that context_loader calls weather MCP when consent is given."""

    # Add routing decision
    initial_state["routing"] = RoutingDecision(
        target_node="agronomist",
        intent=UserIntent.IRRIGATION,
        confidence=0.95,
        requires_context=["user", "farm", "weather"],
    )

    # Mock database calls
    with patch("alim.agent.nodes.context_loader.get_db_session") as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        # Mock user and farm repos
        with patch("alim.agent.nodes.context_loader.UserRepository") as mock_user_repo_class:
            with patch("alim.agent.nodes.context_loader.FarmRepository") as mock_farm_repo_class:
                mock_user_repo = AsyncMock()
                mock_farm_repo = AsyncMock()

                mock_user_repo_class.return_value = mock_user_repo
                mock_farm_repo_class.return_value = mock_farm_repo

                # Mock user data
                mock_user_repo.get_context_for_ai.return_value = {
                    "user_id": "user_456",
                    "display_name": "Farmer Ali",
                    "experience_level": "intermediate",
                    "farm_count": 1,
                }

                # Mock farm data
                mock_farm = AsyncMock()
                mock_farm.farm_id = "farm_123"
                mock_farm.center_coordinates = {
                    "latitude": 40.4,
                    "longitude": 49.9,
                }
                mock_farm_repo.get_primary_farm.return_value = mock_farm
                mock_farm_repo.get_context_for_ai.return_value = {
                    "farm_id": "farm_123",
                    "farm_name": "Pambiq Ferması",
                    "farm_type": "pambiq",
                    "region": "aran",
                    "total_area_ha": 15,
                    "center_coordinates": {"latitude": 40.4, "longitude": 49.9},
                }

                # Mock weather MCP handler
                with patch(
                    "alim.agent.nodes.context_loader.WeatherMCPHandler"
                ) as mock_handler_class:
                    mock_handler = AsyncMock()
                    mock_handler_class.return_value = mock_handler

                    # Mock successful weather forecast
                    mock_handler.get_forecast.return_value = {
                        "current": {
                            "temperature": 28.5,
                            "humidity": 65,
                            "wind_speed": 12,
                            "rainfall_mm": 0,
                        },
                        "forecast": [],
                        "alerts": [],
                    }

                    # Call context_loader
                    result = await context_loader_node(initial_state)

                    # Assertions
                    assert result is not None
                    assert "mcp_traces" in result
                    assert len(result["mcp_traces"]) > 0
                    assert result["mcp_traces"][0]["server"] == "openweather"
                    assert result["mcp_traces"][0]["success"] is True
                    assert "weather" in result
                    assert result["weather"] is not None


@pytest.mark.asyncio
async def test_context_loader_respects_consent(initial_state):
    """Test that weather MCP is not called if user didn't consent."""

    # Mark consent as NOT given
    initial_state["data_consent_given"] = False

    initial_state["routing"] = RoutingDecision(
        target_node="agronomist",
        intent=UserIntent.IRRIGATION,
        confidence=0.95,
        requires_context=["weather"],
    )

    # Mock database
    with patch("alim.agent.nodes.context_loader.get_db_session") as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        with patch("alim.agent.nodes.context_loader.FarmRepository") as mock_farm_repo_class:
            mock_farm_repo = AsyncMock()
            mock_farm_repo_class.return_value = mock_farm_repo

            mock_farm = AsyncMock()
            mock_farm.farm_id = "farm_123"
            mock_farm_repo.get_primary_farm.return_value = mock_farm
            mock_farm_repo.get_context_for_ai.return_value = {
                "farm_id": "farm_123",
                "farm_name": "Test Farm",
                "region": "aran",
            }

            # Mock weather handler should NOT be called
            with patch("alim.agent.nodes.context_loader.WeatherMCPHandler") as mock_handler_class:
                mock_handler = AsyncMock()
                mock_handler_class.return_value = mock_handler

                result = await context_loader_node(initial_state)

                # Weather MCP should not have been called
                mock_handler.get_forecast.assert_not_called()

                # Should use synthetic weather instead
                assert "weather" in result
                assert result["weather"].forecast_summary is not None


@pytest.mark.asyncio
async def test_context_loader_fallback_on_mcp_failure(initial_state):
    """Test fallback to synthetic weather if MCP fails."""

    initial_state["data_consent_given"] = True
    initial_state["routing"] = RoutingDecision(
        target_node="agronomist",
        intent=UserIntent.IRRIGATION,
        confidence=0.95,
        requires_context=["farm", "weather"],
    )

    with patch("alim.agent.nodes.context_loader.get_db_session") as mock_get_db:
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        with patch("alim.agent.nodes.context_loader.FarmRepository") as mock_farm_repo_class:
            mock_farm_repo = AsyncMock()
            mock_farm_repo_class.return_value = mock_farm_repo

            mock_farm = AsyncMock()
            mock_farm.farm_id = "farm_123"
            mock_farm_repo.get_primary_farm.return_value = mock_farm
            mock_farm_repo.get_context_for_ai.return_value = {
                "farm_id": "farm_123",
                "farm_name": "Test Farm",
                "region": "aran",
            }

            # Mock MCP failure
            with patch("alim.agent.nodes.context_loader.WeatherMCPHandler") as mock_handler_class:
                mock_handler = AsyncMock()
                mock_handler_class.return_value = mock_handler
                mock_handler.get_forecast.side_effect = Exception("API error")

                result = await context_loader_node(initial_state)

                # Should have MCP trace with failure
                assert len(result["mcp_traces"]) > 0
                assert result["mcp_traces"][0]["success"] is False

                # Should fallback to synthetic weather
                assert "weather" in result
                assert result["weather"] is not None
                assert result["weather"].forecast_summary is not None
