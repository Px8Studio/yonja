"""
Yonca AI - Sidecar Schedule Service
====================================

Migrated from core/engine.py - contains unique logic for:
1. Daily schedule generation (tasks from recommendations)
2. Alert generation (weather-based warnings)
3. Task duration estimation

This completes the migration from the legacy core module to sidecar architecture.
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from yonca.models import (
    FarmProfile,
    WeatherData,
    Task,
    TaskStatus,
    TaskPriority,
    Alert,
    AlertSeverity,
    DailySchedule,
    Recommendation,
)
from yonca.data.generators import WeatherGenerator
from yonca.sidecar.recommendation_service import (
    SidecarRecommendationService,
    RecommendationRequest,
    RecommendationPriority,
)
from yonca.sidecar.rules_registry import get_rules_registry, RuleCategory


# Task duration estimates by category (in minutes)
TASK_DURATION_ESTIMATES: dict[str, int] = {
    "irrigation": 120,
    "fertilization": 90,
    "pest_control": 60,
    "disease_management": 60,
    "harvest": 240,
    "livestock": 45,
    "soil_management": 120,
    "weather_response": 30,
    "crop_rotation": 180,
    "subsidy": 30,
    "general": 60,
}


class ScheduleService:
    """
    Service for generating daily schedules with tasks and alerts.
    
    This service extends the SidecarRecommendationService by:
    1. Converting recommendations to actionable Task objects
    2. Generating weather-based alerts
    3. Creating complete DailySchedule objects
    
    Usage:
        service = ScheduleService()
        schedule = service.generate_daily_schedule(farm_profile)
    """
    
    def __init__(
        self,
        recommendation_service: Optional[SidecarRecommendationService] = None,
    ):
        """
        Initialize the schedule service.
        
        Args:
            recommendation_service: Underlying recommendation service (created if None)
        """
        self.recommendation_service = recommendation_service or SidecarRecommendationService()
        self.rules_registry = get_rules_registry()
    
    def generate_daily_schedule(
        self,
        farm: FarmProfile,
        target_date: Optional[date] = None,
    ) -> DailySchedule:
        """
        Generate a complete daily schedule with tasks and alerts.
        
        Args:
            farm: The farm profile
            target_date: The date for the schedule (default: today)
            
        Returns:
            Complete daily schedule
        """
        target_date = target_date or date.today()
        
        # Get weather forecast
        weather_forecast = WeatherGenerator.generate(
            target_date,
            farm.location.region,
            days=7
        )
        today_weather = weather_forecast[0] if weather_forecast else None
        
        # Build recommendation request from farm profile
        request = self._build_recommendation_request(farm, today_weather)
        
        # Get recommendations from sidecar service
        response = self.recommendation_service.get_recommendations(request)
        
        # Convert recommendations to tasks
        tasks = self._recommendations_to_tasks(response.recommendations, target_date)
        
        # Generate alerts based on weather
        alerts = self._generate_alerts(farm, today_weather, weather_forecast)
        
        return DailySchedule(
            farm_id=farm.id,
            date=target_date,
            tasks=tasks,
            alerts=alerts,
            weather_forecast=today_weather,
            generated_at=datetime.now(),
        )
    
    def _build_recommendation_request(
        self,
        farm: FarmProfile,
        weather: Optional[WeatherData],
    ) -> RecommendationRequest:
        """Build a RecommendationRequest from FarmProfile."""
        # Extract crop names
        crops = [crop.crop_type for crop in farm.crops]
        
        # Extract livestock types
        livestock_types = [animal.livestock_type.value for animal in farm.livestock]
        
        # Build request
        request = RecommendationRequest(
            farm_id=farm.id,
            region=farm.location.region,
            farm_type=farm.farm_type.value,
            crops=crops,
            livestock_types=livestock_types,
            area_hectares=farm.total_area_hectares,
        )
        
        # Add soil data if available
        if farm.soil_data:
            request.soil_type = farm.soil_data.soil_type.value
            request.soil_moisture_percent = farm.soil_data.moisture_percent
            request.soil_ph = farm.soil_data.ph_level
            request.nitrogen_level = farm.soil_data.nitrogen_level
            request.phosphorus_level = farm.soil_data.phosphorus_level
            request.potassium_level = farm.soil_data.potassium_level
        
        # Add weather data if available
        if weather:
            request.temperature_min = weather.temperature_min
            request.temperature_max = weather.temperature_max
            request.precipitation_expected = weather.condition.value in ["rainy", "stormy"]
            request.humidity_percent = weather.humidity_percent
        
        return request
    
    def _recommendations_to_tasks(
        self,
        recommendations: list,
        target_date: date,
    ) -> list[Task]:
        """Convert recommendation items to Task objects."""
        tasks = []
        
        for rec in recommendations:
            # Map priority from recommendation
            priority = self._map_priority(rec.priority)
            
            # Get estimated duration
            duration = self._estimate_task_duration(rec.type)
            
            task = Task(
                id=f"task-{uuid4().hex[:8]}",
                title=rec.title,
                title_az=rec.title_az,
                description=rec.description,
                description_az=rec.description_az,
                priority=priority,
                status=TaskStatus.PENDING,
                due_date=target_date,
                estimated_duration_minutes=duration,
                category=rec.type,
            )
            tasks.append(task)
        
        return tasks
    
    def _map_priority(self, rec_priority: RecommendationPriority) -> TaskPriority:
        """Map RecommendationPriority to TaskPriority."""
        mapping = {
            RecommendationPriority.CRITICAL: TaskPriority.CRITICAL,
            RecommendationPriority.HIGH: TaskPriority.HIGH,
            RecommendationPriority.MEDIUM: TaskPriority.MEDIUM,
            RecommendationPriority.LOW: TaskPriority.LOW,
        }
        return mapping.get(rec_priority, TaskPriority.MEDIUM)
    
    def _estimate_task_duration(self, task_type: str) -> int:
        """Estimate duration in minutes for a task type."""
        return TASK_DURATION_ESTIMATES.get(task_type, 60)
    
    def _generate_alerts(
        self,
        farm: FarmProfile,
        weather: Optional[WeatherData],
        forecast: list[WeatherData],
    ) -> list[Alert]:
        """Generate alerts based on conditions."""
        alerts = []
        
        if not weather:
            return alerts
        
        # Extreme heat warning (>38°C)
        if weather.temperature_max > 38:
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="weather",
                severity=AlertSeverity.CRITICAL,
                title="Extreme Heat Warning",
                title_az="Həddindən Artıq İsti Xəbərdarlığı",
                message=f"Temperature will reach {weather.temperature_max}°C today. Take precautions for crops and livestock.",
                message_az=f"Bu gün temperatur {weather.temperature_max}°C-yə çatacaq. Bitkilər və heyvanlar üçün ehtiyat tədbirləri görün.",
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(hours=12),
                action_required=True,
            ))
        
        # Storm warning
        if weather.condition.value == "stormy":
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="weather",
                severity=AlertSeverity.WARNING,
                title="Storm Warning",
                title_az="Fırtına Xəbərdarlığı",
                message=f"Storm expected with {weather.precipitation_mm}mm precipitation. Secure equipment and livestock.",
                message_az=f"{weather.precipitation_mm}mm yağıntı ilə fırtına gözlənilir. Avadanlıqları və heyvanları qoruyun.",
                valid_from=datetime.now(),
                action_required=True,
            ))
        
        # Frost warning (<2°C)
        if weather.temperature_min < 2:
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="weather",
                severity=AlertSeverity.WARNING,
                title="Frost Warning",
                title_az="Şaxta Xəbərdarlığı",
                message=f"Temperature may drop to {weather.temperature_min}°C. Protect sensitive crops.",
                message_az=f"Temperatur {weather.temperature_min}°C-yə düşə bilər. Həssas bitkiləri qoruyun.",
                valid_from=datetime.now(),
                action_required=True,
            ))
        
        # Heavy rain warning (>30mm)
        if weather.precipitation_mm > 30:
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="weather",
                severity=AlertSeverity.WARNING,
                title="Heavy Rain Warning",
                title_az="Güclü Yağış Xəbərdarlığı",
                message=f"Heavy rainfall expected: {weather.precipitation_mm}mm. Check drainage and avoid fieldwork.",
                message_az=f"Güclü yağış gözlənilir: {weather.precipitation_mm}mm. Drenajı yoxlayın və tarla işlərindən çəkinin.",
                valid_from=datetime.now(),
                action_required=False,
            ))
        
        # High winds warning (>50 km/h)
        if weather.wind_speed_kmh > 50:
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="weather",
                severity=AlertSeverity.WARNING,
                title="High Wind Warning",
                title_az="Güclü Külək Xəbərdarlığı",
                message=f"Wind speeds up to {weather.wind_speed_kmh} km/h. Secure loose equipment and structures.",
                message_az=f"Küləyin sürəti {weather.wind_speed_kmh} km/saat-a qədər. Boş avadanlıqları və tikililəri möhkəmləndirin.",
                valid_from=datetime.now(),
                action_required=True,
            ))
        
        # Multi-day storm alert (look ahead)
        if any(w.condition.value == "stormy" for w in forecast[:3]):
            storm_days = [w.date for w in forecast[:3] if w.condition.value == "stormy"]
            if storm_days:
                alerts.append(Alert(
                    id=f"alert-{uuid4().hex[:8]}",
                    type="weather",
                    severity=AlertSeverity.INFO,
                    title="Storm Forecast - Next 3 Days",
                    title_az="Fırtına Proqnozu - Növbəti 3 Gün",
                    message=f"Storms expected on: {', '.join(str(d) for d in storm_days)}. Plan harvest accordingly.",
                    message_az=f"Fırtına gözlənilir: {', '.join(str(d) for d in storm_days)}. Məhsul yığımını müvafiq planlaşdırın.",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    action_required=False,
                ))
        
        # UV warning for field workers (UV index > 7)
        if weather.uv_index > 7:
            alerts.append(Alert(
                id=f"alert-{uuid4().hex[:8]}",
                type="health",
                severity=AlertSeverity.WARNING,
                title="High UV Warning",
                title_az="Yüksək UB Xəbərdarlığı",
                message=f"UV index at {weather.uv_index}. Use sun protection for outdoor work.",
                message_az=f"UB indeksi {weather.uv_index}. Açıq havada işləyərkən günəşdən qorunma vasitələrindən istifadə edin.",
                valid_from=datetime.now(),
                action_required=False,
            ))
        
        return alerts


# Singleton instance for convenience
_schedule_service: Optional[ScheduleService] = None


def get_schedule_service() -> ScheduleService:
    """Get the default schedule service singleton."""
    global _schedule_service
    if _schedule_service is None:
        _schedule_service = ScheduleService()
    return _schedule_service


# Convenience function matching old API
def generate_daily_schedule(
    farm: FarmProfile,
    target_date: Optional[date] = None,
) -> DailySchedule:
    """
    Generate a daily schedule for a farm.
    
    This is a convenience function that matches the old core/engine.py API.
    
    Args:
        farm: The farm profile
        target_date: Target date (default: today)
        
    Returns:
        Complete daily schedule with tasks and alerts
    """
    return get_schedule_service().generate_daily_schedule(farm, target_date)
