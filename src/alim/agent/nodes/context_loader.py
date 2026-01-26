# src/ALİM/agent/nodes/context_loader.py
"""Context loader node for loading user and farm data.

Loads context from the database based on the routing decision's requirements.
This keeps context loading separate from business logic nodes.

Phase 2: Integrates real weather data via WeatherMCPHandler
Phase 4.3: Orchestrates parallel Weather + ZekaLab MCP calls with fallbacks
"""

import asyncio
from datetime import UTC
from typing import Any

import structlog

from alim.agent.state import (
    AgentState,
    FarmContext,
    MCPTrace,
    UserContext,
    WeatherContext,
)
from alim.data.cache import CachedFarmRepository, CachedUserRepository
from alim.data.database import get_db_session
from alim.data.repositories.farm_repo import FarmRepository
from alim.data.repositories.user_repo import UserRepository
from alim.mcp.handlers.weather_handler import WeatherMCPHandler
from alim.mcp.handlers.zekalab_handler import get_zekalab_handler

logger = structlog.get_logger(__name__)


async def context_loader_node(state: AgentState) -> dict:
    """Load required context from database and cache.

    Checks the routing decision for what context is needed:
    - "user": Load user profile
    - "farm": Load farm data with parcels
    - "weather": Load weather data (synthetic for now)

    Args:
        state: Current agent state

    Returns:
        State updates with loaded context
    """
    routing = state.get("routing")
    user_id = state.get("user_id")
    nodes_visited = state.get("nodes_visited", []).copy()
    nodes_visited.append("context_loader")

    requires_context = routing.requires_context if routing else []

    logger.info(
        "context_loader_node_start",
        user_id=user_id,
        requires_context=requires_context,
        has_routing=bool(routing),
    )

    updates: dict[str, Any] = {"nodes_visited": nodes_visited}

    # NOTE: Routing logic is now handled by graph.py using the 'routing' state
    # We just focus on loading data here.

    if not routing:
        # Should technically not happen if graph structure is correct,
        # but if it does, the graph edge will handle it (or error out).
        return updates

    async with get_db_session() as session:
        # Load user context
        if "user" in requires_context and user_id:
            # OPTIMIZATION: Check if already loaded in state (persistence)
            if state.get("user_context"):
                logger.info("context_loader_user_cached_in_state")
            else:
                base_user_repo = UserRepository(session)
                user_repo = CachedUserRepository(base_user_repo)
                user_context = await user_repo.get_context_for_ai(user_id)

                if user_context:
                    updates["user_context"] = UserContext(
                        user_id=user_context["user_id"],
                        display_name=user_context["display_name"],
                        experience_level=user_context["experience_level"],
                        preferred_language=user_context.get("preferred_language", "az"),
                        farm_count=user_context.get("farm_count", 0),
                        total_area_ha=user_context.get("total_area_ha", 0.0),
                        primary_activities=user_context.get("primary_activities", []),
                    )

        # Load farm context
        if "farm" in requires_context and user_id:
            # OPTIMIZATION: Check if already loaded in state
            if state.get("farm_context"):
                logger.info("context_loader_farm_cached_in_state")
            else:
                base_farm_repo = FarmRepository(session)
                farm_repo = CachedFarmRepository(base_farm_repo)

                # Get primary farm for user
                primary_farm = await base_farm_repo.get_primary_farm(user_id)

                if primary_farm:
                    farm_context = await farm_repo.get_context_for_ai(primary_farm.farm_id)

                    if farm_context:
                        # Collect alerts from context
                        alerts = farm_context.get("alerts", [])

                        updates["farm_context"] = FarmContext(
                            farm_id=farm_context["farm_id"],
                            farm_name=farm_context["farm_name"],
                            farm_type=farm_context["farm_type"],
                            region=farm_context["region"],
                            total_area_ha=farm_context["total_area_ha"],
                            parcel_count=farm_context.get("parcel_count", 0),
                            parcels=farm_context.get("parcels", []),
                            active_crops=farm_context.get("active_crops", []),
                            alerts=alerts,
                            center_coordinates=farm_context.get("center_coordinates"),
                        )

                        # Merge alerts into state
                        if alerts:
                            updates["alerts"] = alerts

        # Load weather context & ZekaLab rules (Phase 4.3: Parallel MCP Orchestration)
        if "weather" in requires_context or "rules" in requires_context:
            farm_context_obj = updates.get("farm_context") or state.get("farm_context")
            farm_id = farm_context_obj.farm_id if farm_context_obj else None

            mcp_data = await _orchestrate_parallel_mcp(state, farm_id, farm_context_obj)
            updates.update(mcp_data)

    logger.info(
        "context_loader_node_complete",
        user_context_loaded=bool(updates.get("user_context")),
        farm_context_loaded=bool(updates.get("farm_context")),
        weather_loaded=bool(updates.get("weather")),
        mcp_traces_count=len(updates.get("mcp_traces", [])),
    )

    return updates


# ============================================================
# Phase 4.3: Parallel MCP Orchestration
# ============================================================


async def _orchestrate_parallel_mcp(
    state: AgentState, farm_id: str | None, farm_context_obj: FarmContext | None
) -> dict[str, Any]:
    """Orchestrate parallel Weather + ZekaLab MCP calls.

    Returns:
        Dict of state updates (weather, mcp_traces, mcp_context)
    """
    region = farm_context_obj.region if farm_context_obj else "aran"
    mcp_traces = list(state.get("mcp_traces", []))
    use_mcp = state.get("mcp_config", {}).get("use_mcp", True)
    allow_fallback = state.get("mcp_config", {}).get("fallback_to_synthetic", True)
    data_consent = state.get("data_consent_given", False)

    updates: dict[str, Any] = {}
    weather = None
    mcp_context = {}

    if use_mcp and data_consent and farm_id:
        logger.info(
            "mcp_orchestration_start",
            farm_id=farm_id,
            mcp_servers=["openweather", "zekalab"],
        )

        mcp_tasks = []
        mcp_tasks.append(_fetch_weather_mcp(farm_id))

        active_crops = farm_context_obj.active_crops if farm_context_obj else []
        if active_crops:
            crop_type = active_crops[0] if isinstance(active_crops, list) else active_crops
            mcp_tasks.append(_fetch_zekalab_rules_mcp(farm_id, str(crop_type)))
        else:
            mcp_tasks.append(_noop_task("zekalab_rules"))

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*mcp_tasks, return_exceptions=True),
                timeout=5.0,
            )

            # Process Weather
            weather_result = results[0]
            if isinstance(weather_result, tuple) and len(weather_result) == 2:
                forecast_data, weather_trace = weather_result
                mcp_traces.append(weather_trace.model_dump())

                from datetime import datetime

                current = forecast_data.get("current", {})
                weather = WeatherContext(
                    temperature_c=current.get("temperature", 25.0),
                    humidity_percent=current.get("humidity", 60.0),
                    precipitation_mm=current.get("rainfall_mm", 0.0),
                    wind_speed_kmh=current.get("wind_speed", 0.0),
                    forecast_summary=forecast_data.get("forecast_summary"),
                    last_updated=datetime.now(UTC),
                )
            elif isinstance(weather_result, Exception):
                logger.warning("weather_mcp_exception", error=str(weather_result))
                mcp_traces.append(
                    MCPTrace(
                        server="openweather",
                        tool="get_forecast",
                        input_args={"farm_id": farm_id},
                        output={},
                        duration_ms=0,
                        success=False,
                        error_message=str(weather_result),
                    ).model_dump()
                )

            # Process ZekaLab
            if len(results) > 1:
                zekalab_result = results[1]
                if isinstance(zekalab_result, tuple) and len(zekalab_result) == 2:
                    rules_data, rules_trace = zekalab_result
                    mcp_traces.append(rules_trace.model_dump())
                    mcp_context["zekalab_rules"] = rules_data
                elif isinstance(zekalab_result, Exception):
                    logger.warning("zekalab_mcp_exception", error=str(zekalab_result))
                    mcp_traces.append(
                        MCPTrace(
                            server="zekalab",
                            tool="get_rules",
                            input_args={"farm_id": farm_id},
                            output={},
                            duration_ms=0,
                            success=False,
                            error_message=str(zekalab_result),
                        ).model_dump()
                    )

        except (asyncio.TimeoutError, Exception) as e:
            logger.error("mcp_orchestration_failed", error=str(e))
            mcp_traces.append(
                MCPTrace(
                    server="orchestration",
                    tool="parallel_mcp",
                    input_args={"farm_id": farm_id},
                    output={},
                    duration_ms=0,
                    success=False,
                    error_message=str(e),
                ).model_dump()
            )

    if not weather and allow_fallback:
        weather = await _get_synthetic_weather(region)

    if weather:
        updates["weather"] = weather
    if mcp_traces:
        updates["mcp_traces"] = mcp_traces
    if mcp_context:
        updates["mcp_context"] = mcp_context

    return updates


async def _fetch_weather_mcp(farm_id: str) -> tuple[dict[str, Any], MCPTrace]:
    """Fetch weather data from Weather MCP handler.

    Returns:
        Tuple of (weather_data, mcp_trace)
    """
    handler = WeatherMCPHandler()
    try:
        result = await handler.get_forecast(farm_id)
        # Handle both tuple and dict returns
        if isinstance(result, tuple) and len(result) == 2:
            weather_data, trace = result
        else:
            weather_data = result if isinstance(result, dict) else {"raw": str(result)}
            trace = MCPTrace(
                server="weather",
                tool="get_forecast",
                input_args={"farm_id": farm_id},
                output=weather_data,
                duration_ms=0,
                success=True,
            )
        return weather_data, trace

    except Exception as e:  # Catch all exceptions from handler
        logger.error(f"Weather MCP fetch failed: {e}")
        raise


async def _fetch_zekalab_rules_mcp(farm_id: str, crop_type: str):
    """Fetch agricultural rules via ZekaLab MCP (async task).

    Args:
        farm_id: Farm identifier
        crop_type: Crop type for rules

    Returns:
        (rules_data, trace) tuple

    Raises:
        Exception on failure (caught by orchestrator)
    """
    logger.info("zekalab_mcp_start")
    # Ensure handler is correctly instantiated
    handler = await get_zekalab_handler()  # Ensure this is awaited if it's a coroutine
    rules_data, trace = await handler.get_rules_resource()  # Ensure correct parameters are passed
    logger.info("zekalab_mcp_success", farm_id=farm_id, crop_type=crop_type)
    return rules_data, trace


async def _noop_task(task_name: str) -> None:
    """No-op task for conditional MCP calls.

    Args:
        task_name: Task identifier for logging

    Returns:
        None (skipped task)
    """
    logger.debug("mcp_task_skipped", task=task_name)
    return None


async def _get_synthetic_weather(region: str) -> WeatherContext:
    """Generate synthetic weather data for a region.

    TODO: Replace with real weather API integration

    Args:
        region: Agricultural region name

    Returns:
        Synthetic weather context
    """
    import random  # Ensure random is imported
    from datetime import datetime

    # Regional temperature variations (January)
    regional_temps = {
        "aran": (5, 12),
        "ganja_gazakh": (0, 8),
        "shaki_zagatala": (-2, 6),
        "lankaran": (6, 14),
        "guba_khachmaz": (-4, 4),
        "mountainous_shirvan": (-2, 5),
        "upper_karabakh": (-4, 3),
    }

    temp_range = regional_temps.get(region.lower(), (3, 10))
    temperature = random.uniform(*temp_range)

    # Humidity and precipitation
    humidity = random.uniform(50, 80)
    precipitation = random.choice([0, 0, 0, 2, 5, 10])  # Mostly dry

    # Generate summary in Azerbaijani
    summary = ""
    if precipitation > 5:
        summary = "Yağışlı"
    elif temperature < 0:
        summary = "Donlu"
    elif temperature > 30:
        summary = "Çox isti"
    else:
        summary = "Normal"

    return WeatherContext(
        temperature_c=round(temperature, 1),
        humidity_percent=round(humidity, 1),
        precipitation_mm=round(precipitation, 1),
        wind_speed_kmh=round(random.uniform(5, 25), 1),
        forecast_summary=summary,
        last_updated=datetime.now(UTC),
    )
