# src/yonca/agent/nodes/context_loader.py
"""Context loader node for loading user and farm data.

Loads context from the database based on the routing decision's requirements.
This keeps context loading separate from business logic nodes.
"""

from typing import Any

import structlog

from yonca.agent.state import AgentState, FarmContext, UserContext, WeatherContext
from yonca.data.cache import CachedFarmRepository, CachedUserRepository
from yonca.data.database import get_db_session
from yonca.data.repositories.farm_repo import FarmRepository
from yonca.data.repositories.user_repo import UserRepository

logger = structlog.get_logger(__name__)


async def context_loader_node(state: AgentState) -> dict[str, Any]:
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

    if routing is None:
        return updates

    requires_context = routing.requires_context or []

    async with get_db_session() as session:
        # Load user context
        if "user" in requires_context and user_id:
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

        # Load weather context (synthetic for now)
        if "weather" in requires_context:
            # TODO: Integrate with real weather API
            # For now, generate synthetic weather based on region
            farm_context = updates.get("farm_context") or state.get("farm_context")

            if farm_context:
                weather = await _get_synthetic_weather(farm_context.region)
                updates["weather"] = weather
            else:
                # Default weather if no farm context
                updates["weather"] = WeatherContext(
                    temperature_c=25.0,
                    humidity_percent=45.0,
                    precipitation_mm=0.0,
                    wind_speed_kmh=10.0,
                    forecast_summary="Açıq hava, yağış gözlənilmir",
                )

    logger.info(
        "context_loader_node_complete",
        user_context_loaded=bool(updates.get("user_context")),
        farm_context_loaded=bool(updates.get("farm_context")),
        weather_loaded=bool(updates.get("weather")),
    )

    return updates


async def _get_synthetic_weather(region: str) -> WeatherContext:
    """Generate synthetic weather data for a region.

    TODO: Replace with real weather API integration

    Args:
        region: Agricultural region name

    Returns:
        Synthetic weather context
    """
    import random
    from datetime import datetime

    # Regional temperature variations (January)
    regional_temps = {
        "aran": (5, 12),  # Aran - warmer lowlands
        "ganja_gazakh": (0, 8),
        "shaki_zagatala": (-2, 6),
        "lankaran": (6, 14),  # Subtropical
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
    if precipitation > 5:
        summary = "Yağışlı hava gözlənilir"
    elif temperature < 0:
        summary = "Şaxtalı hava, ehtiyatlı olun"
    elif temperature > 30:
        summary = "İsti hava, suvarma tövsiyə olunur"
    else:
        summary = "Müvafiq hava şəraiti"

    return WeatherContext(
        temperature_c=round(temperature, 1),
        humidity_percent=round(humidity, 1),
        precipitation_mm=round(precipitation, 1),
        wind_speed_kmh=round(random.uniform(5, 25), 1),
        forecast_summary=summary,
        last_updated=datetime.utcnow(),
    )


def route_after_context(state: AgentState) -> str:
    """Determine next node after context loading.

    Routes to the target node specified in the routing decision.
    """
    routing = state.get("routing")

    if routing is None:
        return "agronomist"

    return routing.target_node
