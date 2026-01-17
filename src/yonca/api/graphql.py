"""
Yonca AI - GraphQL API
"""
from datetime import date
from typing import Optional
import strawberry
from strawberry.fastapi import GraphQLRouter

from yonca.models import TaskPriority, AlertSeverity, FarmType, Recommendation as ModelRecommendation
from yonca.sidecar import generate_daily_schedule
from yonca.data.scenarios import get_scenario_farms, ALL_SCENARIOS
from yonca.data.generators import generate_weather_forecast
from yonca.sidecar.intent_matcher import get_intent_matcher
from yonca.models import ChatMessage

# Get singleton intent matcher
_intent_matcher = get_intent_matcher()


# ============= GraphQL Types =============

@strawberry.type
class Location:
    region: str
    latitude: float
    longitude: float
    altitude_meters: int


@strawberry.type
class WeatherData:
    date: str
    condition: str
    temperature_min: float
    temperature_max: float
    humidity_percent: int
    precipitation_mm: float
    wind_speed_kmh: float
    uv_index: int


@strawberry.type
class SoilData:
    soil_type: str
    ph_level: float
    moisture_percent: int
    nitrogen_level: float
    phosphorus_level: float
    potassium_level: float


@strawberry.type
class CropInfo:
    crop_type: str
    variety: Optional[str]
    planting_date: str
    expected_harvest_date: Optional[str]
    current_stage: str
    area_hectares: float


@strawberry.type
class LivestockInfo:
    livestock_type: str
    count: int
    average_age_months: int
    health_status: str
    last_vaccination_date: Optional[str]


@strawberry.type
class Task:
    id: str
    title: str
    title_az: str
    description: str
    description_az: str
    priority: str
    status: str
    due_date: str
    estimated_duration_minutes: int
    category: str


@strawberry.type
class Alert:
    id: str
    type: str
    severity: str
    title: str
    title_az: str
    message: str
    message_az: str
    action_required: bool


@strawberry.type
class Recommendation:
    id: str
    farm_id: str
    type: str
    confidence: float
    title: str
    title_az: str
    description: str
    description_az: str
    rationale: str
    rationale_az: str
    priority: str
    suggested_date: str


@strawberry.type
class DailySchedule:
    farm_id: str
    date: str
    tasks: list[Task]
    alerts: list[Alert]
    weather_forecast: Optional[WeatherData]


@strawberry.type
class Farm:
    id: str
    name: str
    farm_type: str
    location: Location
    total_area_hectares: float
    crops: list[CropInfo]
    livestock: list[LivestockInfo]
    soil_data: Optional[SoilData]
    irrigation_system: Optional[str]


@strawberry.type
class ChatResponse:
    message: str
    intent: Optional[str]
    confidence: float
    suggestions: list[str]


@strawberry.type
class FarmRecommendations:
    farm_id: str
    recommendations: list[Recommendation]
    schedule: DailySchedule


# ============= Helper Functions =============

def convert_farm_to_graphql(farm) -> Farm:
    """Convert a FarmProfile to GraphQL Farm type."""
    return Farm(
        id=farm.id,
        name=farm.name,
        farm_type=farm.farm_type.value,
        location=Location(
            region=farm.location.region,
            latitude=farm.location.latitude,
            longitude=farm.location.longitude,
            altitude_meters=farm.location.altitude_meters,
        ),
        total_area_hectares=farm.total_area_hectares,
        crops=[
            CropInfo(
                crop_type=c.crop_type,
                variety=c.variety,
                planting_date=str(c.planting_date),
                expected_harvest_date=str(c.expected_harvest_date) if c.expected_harvest_date else None,
                current_stage=c.current_stage.value,
                area_hectares=c.area_hectares,
            )
            for c in farm.crops
        ],
        livestock=[
            LivestockInfo(
                livestock_type=l.livestock_type.value,
                count=l.count,
                average_age_months=l.average_age_months,
                health_status=l.health_status,
                last_vaccination_date=str(l.last_vaccination_date) if l.last_vaccination_date else None,
            )
            for l in farm.livestock
        ],
        soil_data=SoilData(
            soil_type=farm.soil_data.soil_type.value,
            ph_level=farm.soil_data.ph_level,
            moisture_percent=farm.soil_data.moisture_percent,
            nitrogen_level=farm.soil_data.nitrogen_level,
            phosphorus_level=farm.soil_data.phosphorus_level,
            potassium_level=farm.soil_data.potassium_level,
        ) if farm.soil_data else None,
        irrigation_system=farm.irrigation_system,
    )


def convert_schedule_to_graphql(schedule) -> DailySchedule:
    """Convert a DailySchedule to GraphQL type."""
    return DailySchedule(
        farm_id=schedule.farm_id,
        date=str(schedule.date),
        tasks=[
            Task(
                id=t.id,
                title=t.title,
                title_az=t.title_az,
                description=t.description,
                description_az=t.description_az,
                priority=t.priority.value,
                status=t.status.value,
                due_date=str(t.due_date),
                estimated_duration_minutes=t.estimated_duration_minutes,
                category=t.category,
            )
            for t in schedule.tasks
        ],
        alerts=[
            Alert(
                id=a.id,
                type=a.type,
                severity=a.severity.value,
                title=a.title,
                title_az=a.title_az,
                message=a.message,
                message_az=a.message_az,
                action_required=a.action_required,
            )
            for a in schedule.alerts
        ],
        weather_forecast=WeatherData(
            date=str(schedule.weather_forecast.date),
            condition=schedule.weather_forecast.condition.value,
            temperature_min=schedule.weather_forecast.temperature_min,
            temperature_max=schedule.weather_forecast.temperature_max,
            humidity_percent=schedule.weather_forecast.humidity_percent,
            precipitation_mm=schedule.weather_forecast.precipitation_mm,
            wind_speed_kmh=schedule.weather_forecast.wind_speed_kmh,
            uv_index=schedule.weather_forecast.uv_index,
        ) if schedule.weather_forecast else None,
    )


# ============= GraphQL Query =============

@strawberry.type
class Query:
    @strawberry.field
    def farms(self) -> list[Farm]:
        """Get all available farm profiles."""
        return [convert_farm_to_graphql(f) for f in ALL_SCENARIOS]
    
    @strawberry.field
    def farm(self, farm_id: str) -> Optional[Farm]:
        """Get a specific farm by ID."""
        farms = get_scenario_farms()
        if farm_id in farms:
            return convert_farm_to_graphql(farms[farm_id])
        return None
    
    @strawberry.field
    def farm_recommendations(
        self,
        farm_id: str,
        max_results: int = 10
    ) -> Optional[FarmRecommendations]:
        """Get AI recommendations for a farm."""
        farms = get_scenario_farms()
        
        if farm_id not in farms:
            return None
        
        farm = farms[farm_id]
        
        # Generate schedule (includes tasks as recommendations)
        schedule = generate_daily_schedule(farm)
        
        # Convert tasks to recommendation format for GraphQL compatibility
        recommendations = [
            ModelRecommendation(
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
            for task in schedule.tasks[:max_results]
        ]
        
        return FarmRecommendations(
            farm_id=farm.id,
            recommendations=[
                Recommendation(
                    id=r.id,
                    farm_id=r.farm_id,
                    type=r.type,
                    confidence=r.confidence,
                    title=r.title,
                    title_az=r.title_az,
                    description=r.description,
                    description_az=r.description_az,
                    rationale=r.rationale,
                    rationale_az=r.rationale_az,
                    priority=r.priority.value,
                    suggested_date=str(r.suggested_date),
                )
                for r in recommendations
            ],
            schedule=convert_schedule_to_graphql(schedule),
        )
    
    @strawberry.field
    def daily_schedule(self, farm_id: str) -> Optional[DailySchedule]:
        """Get the daily schedule for a farm."""
        farms = get_scenario_farms()
        
        if farm_id not in farms:
            return None
        
        farm = farms[farm_id]
        schedule = generate_daily_schedule(farm)
        
        return convert_schedule_to_graphql(schedule)
    
    @strawberry.field
    def weather_forecast(self, region: str, days: int = 7) -> list[WeatherData]:
        """Get weather forecast for a region."""
        forecast = generate_weather_forecast(region, days)
        
        return [
            WeatherData(
                date=str(w.date),
                condition=w.condition.value,
                temperature_min=w.temperature_min,
                temperature_max=w.temperature_max,
                humidity_percent=w.humidity_percent,
                precipitation_mm=w.precipitation_mm,
                wind_speed_kmh=w.wind_speed_kmh,
                uv_index=w.uv_index,
            )
            for w in forecast
        ]
    
    @strawberry.field
    def today_alerts(self, farm_id: Optional[str] = None) -> list[Alert]:
        """Get today's alerts, optionally filtered by farm."""
        farms_to_check = []
        
        if farm_id:
            farms = get_scenario_farms()
            if farm_id in farms:
                farms_to_check = [farms[farm_id]]
        else:
            farms_to_check = ALL_SCENARIOS
        
        all_alerts = []
        for farm in farms_to_check:
            schedule = generate_daily_schedule(farm)
            for a in schedule.alerts:
                all_alerts.append(Alert(
                    id=a.id,
                    type=a.type,
                    severity=a.severity.value,
                    title=a.title,
                    title_az=a.title_az,
                    message=a.message,
                    message_az=a.message_az,
                    action_required=a.action_required,
                ))
        
        return all_alerts


# ============= GraphQL Mutation =============

@strawberry.type
class Mutation:
    @strawberry.mutation
    def send_chat_message(
        self,
        message: str,
        farm_id: Optional[str] = None,
        language: str = "az"
    ) -> ChatResponse:
        """Send a message to the Yonca AI chatbot."""
        # Use unified intent matcher
        intent_result = _intent_matcher.match(message)
        
        suggestions = []
        if intent_result.intent == "general":
            suggestions = [
                "Suvarma haqqında soruşun",
                "Gübrələmə tövsiyəsi", 
                "Hava proqnozu",
            ]
        
        return ChatResponse(
            message=f"Intent: {intent_result.intent}",
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            suggestions=suggestions,
        )


# ============= Schema & Router =============

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
