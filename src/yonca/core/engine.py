"""
Yonca AI - Recommendation Engine

⚠️ DEPRECATION NOTICE ⚠️
========================
This module is DEPRECATED and will be removed in a future release.

Migration Guide:
----------------
- For recommendations: Use `yonca.sidecar.recommendation_service.SidecarRecommendationService`
- For daily schedules: Use `yonca.sidecar.schedule_service.ScheduleService`
- For rules: Use `yonca.sidecar.rules_registry`

The unique logic from this module has been migrated to:
- `sidecar/schedule_service.py` - DailySchedule, Task conversion, Alerts
- `sidecar/rules_registry.py` - All agronomy rules with AZ- prefixes

Example migration:
    # Old (deprecated):
    from yonca.core.engine import recommendation_engine
    schedule = recommendation_engine.generate_daily_schedule(farm)
    
    # New (recommended):
    from yonca.sidecar import generate_daily_schedule
    schedule = generate_daily_schedule(farm)

AI-driven recommendation system for farm operations.
"""
import warnings
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from yonca.models import (
    FarmProfile, FarmType, WeatherData, CropStage, TaskPriority,
    Task, TaskStatus, Alert, AlertSeverity, Recommendation,
    DailySchedule, CropInfo, LivestockInfo
)
from yonca.core.rules import (
    ALL_RULES, get_rules_by_farm_type, Rule,
    IRRIGATION_RULES, FERTILIZATION_RULES, PEST_DISEASE_RULES,
    HARVEST_RULES, LIVESTOCK_RULES
)
from yonca.data.generators import WeatherGenerator
from yonca.config import settings


class RecommendationEngine:
    """
    AI-driven recommendation engine for farm operations.
    Uses rule-based logic to generate contextual recommendations.
    
    ⚠️ DEPRECATED: Use yonca.sidecar.SidecarRecommendationService instead.
    """
    
    def __init__(self):
        warnings.warn(
            "RecommendationEngine is deprecated. "
            "Use yonca.sidecar.SidecarRecommendationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.rules = ALL_RULES
        
    def generate_recommendations(
        self,
        farm: FarmProfile,
        target_date: Optional[date] = None,
        weather_forecast: Optional[list[WeatherData]] = None,
        max_recommendations: int = 10
    ) -> list[Recommendation]:
        """
        Generate AI recommendations for a farm based on current conditions.
        
        Args:
            farm: The farm profile to generate recommendations for
            target_date: The date to generate recommendations for (default: today)
            weather_forecast: Weather forecast data (generated if not provided)
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of prioritized recommendations
        """
        target_date = target_date or date.today()
        
        # Generate weather if not provided
        if not weather_forecast:
            weather_forecast = WeatherGenerator.generate(
                target_date,
                farm.location.region,
                days=7
            )
        
        today_weather = weather_forecast[0] if weather_forecast else None
        
        recommendations: list[Recommendation] = []
        applicable_rules = get_rules_by_farm_type(farm.farm_type)
        
        # Process irrigation rules
        if farm.soil_data and today_weather:
            recommendations.extend(
                self._evaluate_irrigation_rules(farm, today_weather)
            )
        
        # Process fertilization rules
        if farm.soil_data and farm.crops:
            recommendations.extend(
                self._evaluate_fertilization_rules(farm)
            )
        
        # Process pest/disease rules
        if today_weather and farm.crops:
            recommendations.extend(
                self._evaluate_pest_rules(farm, today_weather)
            )
        
        # Process harvest rules
        if today_weather and farm.crops:
            recommendations.extend(
                self._evaluate_harvest_rules(farm, today_weather, weather_forecast)
            )
        
        # Process livestock rules
        if farm.livestock and today_weather:
            recommendations.extend(
                self._evaluate_livestock_rules(farm, today_weather)
            )
        
        # Sort by priority and confidence
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        recommendations.sort(
            key=lambda r: (priority_order[r.priority], -r.confidence)
        )
        
        return recommendations[:max_recommendations]
    
    def _evaluate_irrigation_rules(
        self,
        farm: FarmProfile,
        weather: WeatherData
    ) -> list[Recommendation]:
        """Evaluate irrigation rules and generate recommendations."""
        recommendations = []
        soil = farm.soil_data
        
        if not soil:
            return recommendations
        
        # Rule: Low soil moisture
        if soil.moisture_percent < 30 and weather.condition not in ["rainy", "stormy"]:
            for crop in farm.crops:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="irrigation",
                    confidence=0.92,
                    title=f"Irrigate {crop.crop_type} field",
                    title_az=f"{crop.crop_type} sahəsini suvarın",
                    description=f"Soil moisture at {soil.moisture_percent}% - below optimal threshold of 30%",
                    description_az=f"Torpaq nəmliyi {soil.moisture_percent}% - optimal həddən (30%) aşağı",
                    rationale="Low soil moisture can stress plants and reduce yields. Immediate irrigation recommended.",
                    rationale_az="Aşağı torpaq nəmliyi bitkiləri stresə sala və məhsuldarlığı azalda bilər. Təcili suvarma tövsiyə olunur.",
                    priority=TaskPriority.HIGH,
                    suggested_date=date.today(),
                ))
        
        # Rule: Heat wave irrigation
        if weather.temperature_max > 35 and soil.moisture_percent < 50:
            recommendations.append(Recommendation(
                id=f"rec-{uuid4().hex[:8]}",
                farm_id=farm.id,
                type="irrigation",
                confidence=0.95,
                title="Emergency irrigation - extreme heat",
                title_az="Təcili suvarma - həddindən artıq isti",
                description=f"Temperature {weather.temperature_max}°C with low moisture",
                description_az=f"Temperatur {weather.temperature_max}°C aşağı nəmliklə",
                rationale="Extreme heat combined with low moisture can cause permanent crop damage.",
                rationale_az="Həddindən artıq isti və aşağı nəmlik daimi bitki zədəsinə səbəb ola bilər.",
                priority=TaskPriority.CRITICAL,
                suggested_date=date.today(),
            ))
        
        # Rule: Skip irrigation before rain
        if weather.condition in ["rainy", "stormy"] and soil.moisture_percent < 45:
            recommendations.append(Recommendation(
                id=f"rec-{uuid4().hex[:8]}",
                farm_id=farm.id,
                type="irrigation",
                confidence=0.88,
                title="Postpone irrigation - rain expected",
                title_az="Suvarmanı təxirə salın - yağış gözlənilir",
                description=f"Expected precipitation: {weather.precipitation_mm}mm",
                description_az=f"Gözlənilən yağıntı: {weather.precipitation_mm}mm",
                rationale="Rain will naturally replenish soil moisture, saving water and costs.",
                rationale_az="Yağış torpaq nəmliyini təbii şəkildə bərpa edəcək, su və xərcə qənaət edəcək.",
                priority=TaskPriority.MEDIUM,
                suggested_date=date.today(),
            ))
        
        return recommendations
    
    def _evaluate_fertilization_rules(
        self,
        farm: FarmProfile
    ) -> list[Recommendation]:
        """Evaluate fertilization rules and generate recommendations."""
        recommendations = []
        soil = farm.soil_data
        
        if not soil:
            return recommendations
        
        for crop in farm.crops:
            # Rule: Low nitrogen during vegetative growth
            if soil.nitrogen_level < 30 and crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING]:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="fertilization",
                    confidence=0.90,
                    title=f"Apply nitrogen fertilizer to {crop.crop_type}",
                    title_az=f"{crop.crop_type} üçün azot gübrəsi tətbiq edin",
                    description=f"Nitrogen at {soil.nitrogen_level} kg/ha during {crop.current_stage.value} stage",
                    description_az=f"{crop.current_stage.value} mərhələsində azot {soil.nitrogen_level} kq/ha",
                    rationale="Adequate nitrogen is essential for leaf and stem development.",
                    rationale_az="Yarpaq və gövdə inkişafı üçün kifayət qədər azot vacibdir.",
                    priority=TaskPriority.HIGH,
                    suggested_date=date.today() + timedelta(days=2),
                ))
            
            # Rule: Phosphorus for flowering
            if soil.phosphorus_level < 25 and crop.current_stage == CropStage.FLOWERING:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="fertilization",
                    confidence=0.87,
                    title=f"Apply phosphorus to {crop.crop_type}",
                    title_az=f"{crop.crop_type}-a fosfor tətbiq edin",
                    description=f"Phosphorus at {soil.phosphorus_level} kg/ha during flowering",
                    description_az=f"Çiçəkləmə zamanı fosfor {soil.phosphorus_level} kq/ha",
                    rationale="Phosphorus supports flower and fruit development.",
                    rationale_az="Fosfor çiçək və meyvə inkişafını dəstəkləyir.",
                    priority=TaskPriority.MEDIUM,
                    suggested_date=date.today() + timedelta(days=3),
                ))
            
            # Rule: Potassium before harvest
            if soil.potassium_level < 100 and crop.current_stage in [CropStage.FRUITING, CropStage.MATURITY]:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="fertilization",
                    confidence=0.85,
                    title=f"Apply potassium to {crop.crop_type}",
                    title_az=f"{crop.crop_type}-a kalium tətbiq edin",
                    description=f"Potassium at {soil.potassium_level} kg/ha - boost fruit quality",
                    description_az=f"Kalium {soil.potassium_level} kq/ha - meyvə keyfiyyətini artırın",
                    rationale="Potassium improves fruit size, color, and storage quality.",
                    rationale_az="Kalium meyvə ölçüsünü, rəngini və saxlama keyfiyyətini yaxşılaşdırır.",
                    priority=TaskPriority.MEDIUM,
                    suggested_date=date.today() + timedelta(days=5),
                ))
        
        return recommendations
    
    def _evaluate_pest_rules(
        self,
        farm: FarmProfile,
        weather: WeatherData
    ) -> list[Recommendation]:
        """Evaluate pest and disease rules."""
        recommendations = []
        
        for crop in farm.crops:
            # Rule: High humidity fungal risk
            if weather.humidity_percent > 75 and crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING, CropStage.FRUITING]:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="pest_control",
                    confidence=0.83,
                    title=f"Monitor {crop.crop_type} for fungal diseases",
                    title_az=f"{crop.crop_type}-ı göbələk xəstəlikləri üçün izləyin",
                    description=f"Humidity at {weather.humidity_percent}% - increased fungal risk",
                    description_az=f"Rütubət {weather.humidity_percent}% - göbələk riski artıb",
                    rationale="High humidity creates favorable conditions for fungal pathogens.",
                    rationale_az="Yüksək rütubət göbələk patogenləri üçün əlverişli şərait yaradır.",
                    priority=TaskPriority.HIGH,
                    suggested_date=date.today(),
                ))
            
            # Rule: Aphid risk in warm dry conditions
            if weather.temperature_max > 25 and weather.humidity_percent < 50:
                if crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING]:
                    recommendations.append(Recommendation(
                        id=f"rec-{uuid4().hex[:8]}",
                        farm_id=farm.id,
                        type="pest_control",
                        confidence=0.78,
                        title=f"Check {crop.crop_type} for aphids",
                        title_az=f"{crop.crop_type}-ı mənənə üçün yoxlayın",
                        description="Warm, dry conditions favor aphid populations",
                        description_az="İsti, quru şərait mənənə populyasiyasına əlverişlidir",
                        rationale="Aphids thrive in warm, dry weather and can quickly damage crops.",
                        rationale_az="Mənənələr isti, quru havada inkişaf edir və bitkilərə tez zərər verə bilər.",
                        priority=TaskPriority.MEDIUM,
                        suggested_date=date.today(),
                    ))
        
        return recommendations
    
    def _evaluate_harvest_rules(
        self,
        farm: FarmProfile,
        weather: WeatherData,
        forecast: list[WeatherData]
    ) -> list[Recommendation]:
        """Evaluate harvest timing rules."""
        recommendations = []
        
        for crop in farm.crops:
            # Rule: Mature crop ready for harvest
            if crop.current_stage == CropStage.MATURITY:
                if weather.condition not in ["rainy", "stormy"]:
                    recommendations.append(Recommendation(
                        id=f"rec-{uuid4().hex[:8]}",
                        farm_id=farm.id,
                        type="harvest",
                        confidence=0.95,
                        title=f"Harvest {crop.crop_type} - optimal conditions",
                        title_az=f"{crop.crop_type} məhsulunu yığın - optimal şərait",
                        description="Crop at maturity with favorable weather",
                        description_az="Bitki yetişib, hava əlverişlidir",
                        rationale="Harvesting at maturity ensures best quality and yield.",
                        rationale_az="Yetişmə zamanı məhsul yığımı ən yaxşı keyfiyyət və məhsuldarlığı təmin edir.",
                        priority=TaskPriority.CRITICAL,
                        suggested_date=date.today(),
                    ))
                
                # Check for incoming storms
                if any(w.condition == "stormy" for w in forecast[:3]):
                    recommendations.append(Recommendation(
                        id=f"rec-{uuid4().hex[:8]}",
                        farm_id=farm.id,
                        type="harvest",
                        confidence=0.98,
                        title=f"URGENT: Harvest {crop.crop_type} before storm",
                        title_az=f"TƏCİLİ: Fırtınadan əvvəl {crop.crop_type} yığın",
                        description="Storm expected within 3 days",
                        description_az="3 gün ərzində fırtına gözlənilir",
                        rationale="Delaying harvest may result in significant crop damage or loss.",
                        rationale_az="Məhsul yığımını gecikdirmək ciddi zərər və ya itki ilə nəticələnə bilər.",
                        priority=TaskPriority.CRITICAL,
                        suggested_date=date.today(),
                    ))
        
        return recommendations
    
    def _evaluate_livestock_rules(
        self,
        farm: FarmProfile,
        weather: WeatherData
    ) -> list[Recommendation]:
        """Evaluate livestock management rules."""
        recommendations = []
        
        for animal in farm.livestock:
            # Rule: Heat stress
            if weather.temperature_max > 32:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="livestock",
                    confidence=0.93,
                    title=f"Heat protection for {animal.livestock_type.value}",
                    title_az=f"{animal.livestock_type.value} üçün isti mühafizəsi",
                    description=f"Temperature {weather.temperature_max}°C - heat stress risk",
                    description_az=f"Temperatur {weather.temperature_max}°C - isti stresi riski",
                    rationale="Extreme heat can cause heat stress, reduced productivity, and death.",
                    rationale_az="Həddindən artıq isti stres, azalmış məhsuldarlıq və ölümə səbəb ola bilər.",
                    priority=TaskPriority.CRITICAL,
                    suggested_date=date.today(),
                ))
            
            # Rule: Cold weather shelter
            if weather.temperature_min < 5:
                recommendations.append(Recommendation(
                    id=f"rec-{uuid4().hex[:8]}",
                    farm_id=farm.id,
                    type="livestock",
                    confidence=0.90,
                    title=f"Cold shelter for {animal.livestock_type.value}",
                    title_az=f"{animal.livestock_type.value} üçün soyuq sığınacağı",
                    description=f"Temperature dropping to {weather.temperature_min}°C",
                    description_az=f"Temperatur {weather.temperature_min}°C-yə düşür",
                    rationale="Cold exposure can lead to illness and reduced productivity.",
                    rationale_az="Soyuğa məruz qalma xəstəlik və azalmış məhsuldarlığa səbəb ola bilər.",
                    priority=TaskPriority.HIGH,
                    suggested_date=date.today(),
                ))
            
            # Rule: Vaccination reminder
            if animal.last_vaccination_date:
                days_since = (date.today() - animal.last_vaccination_date).days
                if days_since > 180:
                    recommendations.append(Recommendation(
                        id=f"rec-{uuid4().hex[:8]}",
                        farm_id=farm.id,
                        type="livestock",
                        confidence=0.95,
                        title=f"Vaccination overdue for {animal.livestock_type.value}",
                        title_az=f"{animal.livestock_type.value} üçün peyvənd gecikib",
                        description=f"Last vaccination {days_since} days ago",
                        description_az=f"Son peyvənd {days_since} gün əvvəl",
                        rationale="Regular vaccination prevents disease outbreaks.",
                        rationale_az="Müntəzəm peyvənd xəstəlik yayılmasının qarşısını alır.",
                        priority=TaskPriority.HIGH,
                        suggested_date=date.today() + timedelta(days=7),
                    ))
        
        return recommendations
    
    def generate_daily_schedule(
        self,
        farm: FarmProfile,
        target_date: Optional[date] = None
    ) -> DailySchedule:
        """
        Generate a complete daily schedule with tasks and alerts.
        
        Args:
            farm: The farm profile
            target_date: The date for the schedule
            
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
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            farm, target_date, weather_forecast
        )
        
        # Convert recommendations to tasks
        tasks = []
        for rec in recommendations:
            tasks.append(Task(
                id=f"task-{uuid4().hex[:8]}",
                title=rec.title,
                title_az=rec.title_az,
                description=rec.description,
                description_az=rec.description_az,
                priority=rec.priority,
                status=TaskStatus.PENDING,
                due_date=rec.suggested_date,
                estimated_duration_minutes=self._estimate_task_duration(rec.type),
                category=rec.type,
            ))
        
        # Generate alerts
        alerts = self._generate_alerts(farm, today_weather, weather_forecast)
        
        return DailySchedule(
            farm_id=farm.id,
            date=target_date,
            tasks=tasks,
            alerts=alerts,
            weather_forecast=today_weather,
        )
    
    def _estimate_task_duration(self, task_type: str) -> int:
        """Estimate duration in minutes for a task type."""
        durations = {
            "irrigation": 120,
            "fertilization": 90,
            "pest_control": 60,
            "harvest": 240,
            "livestock": 45,
            "subsidy": 30,
        }
        return durations.get(task_type, 60)
    
    def _generate_alerts(
        self,
        farm: FarmProfile,
        weather: Optional[WeatherData],
        forecast: list[WeatherData]
    ) -> list[Alert]:
        """Generate alerts based on conditions."""
        alerts = []
        
        if weather:
            # Weather alerts
            if weather.temperature_max > 38:
                alerts.append(Alert(
                    id=f"alert-{uuid4().hex[:8]}",
                    type="weather",
                    severity=AlertSeverity.CRITICAL,
                    title="Extreme Heat Warning",
                    title_az="Həddindən Artıq İsti Xəbərdarlığı",
                    message=f"Temperature will reach {weather.temperature_max}°C today",
                    message_az=f"Bu gün temperatur {weather.temperature_max}°C-yə çatacaq",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(hours=12),
                    action_required=True,
                ))
            
            if weather.condition == "stormy":
                alerts.append(Alert(
                    id=f"alert-{uuid4().hex[:8]}",
                    type="weather",
                    severity=AlertSeverity.WARNING,
                    title="Storm Warning",
                    title_az="Fırtına Xəbərdarlığı",
                    message=f"Storm expected with {weather.precipitation_mm}mm precipitation",
                    message_az=f"{weather.precipitation_mm}mm yağıntı ilə fırtına gözlənilir",
                    valid_from=datetime.now(),
                    action_required=True,
                ))
            
            # Frost alert
            if weather.temperature_min < 2:
                alerts.append(Alert(
                    id=f"alert-{uuid4().hex[:8]}",
                    type="weather",
                    severity=AlertSeverity.WARNING,
                    title="Frost Warning",
                    title_az="Şaxta Xəbərdarlığı",
                    message=f"Temperature may drop to {weather.temperature_min}°C",
                    message_az=f"Temperatur {weather.temperature_min}°C-yə düşə bilər",
                    valid_from=datetime.now(),
                    action_required=True,
                ))
        
        return alerts


# Singleton instance
recommendation_engine = RecommendationEngine()
