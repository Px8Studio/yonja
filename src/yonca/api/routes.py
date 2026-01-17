"""
Yonca AI - REST API Routes
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from yonca.models import (
    RecommendationRequest, RecommendationResponse, 
    ChatMessage, ChatResponse, DailySchedule, FarmProfile,
    Alert
)
from yonca.sidecar import generate_daily_schedule, get_schedule_service
from yonca.sidecar.intent_matcher import get_intent_matcher
from yonca.data.scenarios import get_scenario_farms, ALL_SCENARIOS
from yonca.data.generators import generate_weather_forecast


router = APIRouter(tags=["Yonca AI"])

# Get singleton intent matcher
_intent_matcher = get_intent_matcher()


# ============= Farm Endpoints =============

@router.get("/farms", response_model=list[FarmProfile])
async def list_farms():
    """
    Get all available farm profiles.
    Returns pre-defined scenario farms for demonstration.
    """
    return ALL_SCENARIOS


@router.get("/farms/{farm_id}", response_model=FarmProfile)
async def get_farm(farm_id: str):
    """
    Get a specific farm profile by ID.
    """
    farms = get_scenario_farms()
    if farm_id not in farms:
        raise HTTPException(status_code=404, detail=f"Farm '{farm_id}' not found")
    return farms[farm_id]


# ============= Recommendation Endpoints =============

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get AI-powered recommendations for a farm.
    
    The recommendation engine analyzes:
    - Current weather conditions
    - Soil moisture and nutrients
    - Crop growth stages
    - Livestock health status
    
    Returns prioritized recommendations for farm operations.
    """
    farms = get_scenario_farms()
    
    if request.farm_id not in farms:
        raise HTTPException(status_code=404, detail=f"Farm '{request.farm_id}' not found")
    
    farm = farms[request.farm_id]
    target_date = request.date or date.today()
    
    # Generate weather forecast
    weather_forecast = generate_weather_forecast(
        farm.location.region,
        days=7
    )
    
    # Generate daily schedule (includes recommendations as tasks)
    daily_schedule = generate_daily_schedule(
        farm=farm,
        target_date=target_date
    )
    
    # Extract recommendations from tasks for API compatibility
    from yonca.models import Recommendation
    recommendations = [
        Recommendation(
            id=task.id.replace('task-', 'rec-'),
            farm_id=farm.id,
            type=task.category,
            confidence=0.85,
            title=task.title,
            title_az=task.title_az,
            description=task.description,
            description_az=task.description_az,
            rationale=task.description,
            rationale_az=task.description_az,
            priority=task.priority,
            suggested_date=task.due_date,
        )
        for task in daily_schedule.tasks[:request.max_results]
    ]
    
    return RecommendationResponse(
        farm_id=farm.id,
        recommendations=recommendations,
        daily_schedule=daily_schedule,
    )


@router.get("/farms/{farm_id}/schedule", response_model=DailySchedule)
async def get_daily_schedule(
    farm_id: str,
    target_date: Optional[date] = Query(default=None, description="Date for schedule (default: today)")
):
    """
    Get the daily schedule for a farm.
    
    Returns a complete list of tasks and alerts for the specified date.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        raise HTTPException(status_code=404, detail=f"Farm '{farm_id}' not found")
    
    farm = farms[farm_id]
    
    return generate_daily_schedule(
        farm=farm,
        target_date=target_date or date.today()
    )


@router.get("/alerts/today", response_model=list[Alert])
async def get_today_alerts(
    farm_id: Optional[str] = Query(default=None, description="Filter by farm ID")
):
    """
    Get all alerts for today.
    
    Optionally filter by farm ID to get farm-specific alerts.
    """
    farms_to_check = []
    
    if farm_id:
        farms = get_scenario_farms()
        if farm_id not in farms:
            raise HTTPException(status_code=404, detail=f"Farm '{farm_id}' not found")
        farms_to_check = [farms[farm_id]]
    else:
        farms_to_check = ALL_SCENARIOS
    
    all_alerts = []
    for farm in farms_to_check:
        schedule = generate_daily_schedule(farm)
        all_alerts.extend(schedule.alerts)
    
    return all_alerts


# ============= Chatbot Endpoints =============

@router.post("/chatbot/message", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Send a message to the Yonca AI chatbot.
    
    The chatbot understands Azerbaijani and can help with:
    - Irrigation advice (suvarma)
    - Fertilization recommendations (gübrələmə)
    - Pest/disease alerts (xəstəlik, zərərverici)
    - Harvest timing (məhsul yığımı)
    - Weather information (hava)
    - Livestock care (heyvandarlıq)
    - Subsidy information (subsidiya)
    - Daily schedule (cədvəl)
    
    Example messages:
    - "Salam, nə vaxt suvarmalıyam?"
    - "Bu gün üçün plan nədir?"
    - "Gübrə lazımdırmı?"
    """
    # Use unified intent matcher
    intent_result = _intent_matcher.match(message.message)
    
    # Generate response based on intent
    suggestions = []
    if intent_result.intent == "general":
        suggestions = [
            "Suvarma haqqında soruşun",
            "Gübrələmə tövsiyəsi",
            "Hava proqnozu",
            "Gündəlik plan",
        ]
    
    return ChatResponse(
        message=f"Intent: {intent_result.intent}",
        intent=intent_result.intent,
        confidence=intent_result.confidence,
        suggestions=suggestions,
        related_tasks=[],
    )


# ============= Weather Endpoints =============

@router.get("/weather/{region}")
async def get_weather(
    region: str,
    days: int = Query(default=7, ge=1, le=14, description="Number of forecast days")
):
    """
    Get weather forecast for a region.
    
    Available regions:
    - Aran
    - Şəki-Zaqatala
    - Lənkəran
    - Abşeron
    - Gəncə-Qazax
    - Mil-Muğan
    - Şirvan
    - Quba-Xaçmaz
    """
    valid_regions = [
        "Aran", "Şəki-Zaqatala", "Lənkəran", "Abşeron",
        "Gəncə-Qazax", "Mil-Muğan", "Şirvan", "Quba-Xaçmaz"
    ]
    
    if region not in valid_regions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region. Valid regions: {', '.join(valid_regions)}"
        )
    
    return generate_weather_forecast(region, days)


# ============= Health & Info Endpoints =============

@router.get("/info")
async def api_info():
    """
    Get API information and available endpoints.
    """
    return {
        "name": "Yonca AI API",
        "version": "0.1.0",
        "description": "AI-driven daily farm planning assistant",
        "endpoints": {
            "farms": "GET /api/v1/farms - List all farms",
            "farm_detail": "GET /api/v1/farms/{farm_id} - Get farm details",
            "recommendations": "POST /api/v1/recommendations - Get AI recommendations",
            "schedule": "GET /api/v1/farms/{farm_id}/schedule - Get daily schedule",
            "alerts": "GET /api/v1/alerts/today - Get today's alerts",
            "chatbot": "POST /api/v1/chatbot/message - Chat with AI assistant",
            "weather": "GET /api/v1/weather/{region} - Get weather forecast",
        },
        "supported_farm_types": ["wheat", "livestock", "orchard", "vegetable", "mixed"],
        "supported_languages": ["az", "en"],
    }
