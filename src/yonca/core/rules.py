"""
Yonca AI - Rule-Based Recommendation Rules
Defines agricultural rules for different scenarios.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from yonca.models import (
    CropStage, FarmType, SoilType, WeatherCondition, 
    TaskPriority, AlertSeverity
)


@dataclass
class Rule:
    """A single recommendation rule."""
    id: str
    name: str
    name_az: str
    description: str
    description_az: str
    category: str
    farm_types: list[FarmType]
    priority: TaskPriority
    condition: Callable[..., bool]
    action_template: str
    action_template_az: str


# ============= Irrigation Rules =============

IRRIGATION_RULES = [
    Rule(
        id="IRR-001",
        name="Low Soil Moisture Irrigation",
        name_az="Aşağı torpaq nəmliyi suvarması",
        description="Irrigate when soil moisture drops below 30%",
        description_az="Torpaq nəmliyi 30%-dən aşağı düşdükdə suvarın",
        category="irrigation",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.HIGH,
        condition=lambda soil, weather: (
            soil.moisture_percent < 30 and
            weather.condition not in [WeatherCondition.RAINY, WeatherCondition.STORMY]
        ),
        action_template="Irrigate {crop} field - soil moisture at {moisture}%",
        action_template_az="{crop} sahəsini suvarın - torpaq nəmliyi {moisture}%",
    ),
    Rule(
        id="IRR-002",
        name="Pre-Rain Irrigation Skip",
        name_az="Yağışdan əvvəl suvarmanı keçin",
        description="Skip irrigation if rain expected within 24 hours",
        description_az="24 saat ərzində yağış gözlənilirsə, suvarmanı keçin",
        category="irrigation",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.MEDIUM,
        condition=lambda soil, weather: (
            soil.moisture_percent < 40 and
            weather.condition in [WeatherCondition.RAINY, WeatherCondition.STORMY]
        ),
        action_template="Skip irrigation - rain expected ({precipitation}mm)",
        action_template_az="Suvarmanı keçin - yağış gözlənilir ({precipitation}mm)",
    ),
    Rule(
        id="IRR-003",
        name="Heat Wave Irrigation",
        name_az="İsti dalğası suvarması",
        description="Increase irrigation during extreme heat",
        description_az="Həddindən artıq istidə suvarmanı artırın",
        category="irrigation",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.CRITICAL,
        condition=lambda soil, weather: (
            weather.temperature_max > 35 and
            soil.moisture_percent < 50
        ),
        action_template="Urgent: Increase irrigation - temperature {temp}°C",
        action_template_az="Təcili: Suvarmanı artırın - temperatur {temp}°C",
    ),
    Rule(
        id="IRR-004",
        name="Early Morning Irrigation",
        name_az="Səhər tezdən suvarma",
        description="Recommend early morning irrigation to reduce evaporation",
        description_az="Buxarlanmanı azaltmaq üçün səhər tezdən suvarma tövsiyə olunur",
        category="irrigation",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.MEDIUM,
        condition=lambda soil, weather: (
            weather.temperature_max > 30 and
            weather.condition == WeatherCondition.SUNNY
        ),
        action_template="Schedule irrigation for early morning (6-8 AM)",
        action_template_az="Suvarmanı səhər saatlarına (6-8) planlaşdırın",
    ),
]


# ============= Fertilization Rules =============

FERTILIZATION_RULES = [
    Rule(
        id="FERT-001",
        name="Low Nitrogen Fertilization",
        name_az="Aşağı azot gübrələməsi",
        description="Apply nitrogen fertilizer when levels are low",
        description_az="Azot səviyyəsi aşağı olduqda gübrə tətbiq edin",
        category="fertilization",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.HIGH,
        condition=lambda soil, crop: (
            soil.nitrogen_level < 30 and
            crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING]
        ),
        action_template="Apply nitrogen fertilizer to {crop} - current level {n_level} kg/ha",
        action_template_az="{crop} üçün azot gübrəsi tətbiq edin - cari səviyyə {n_level} kq/ha",
    ),
    Rule(
        id="FERT-002",
        name="Phosphorus Boost for Flowering",
        name_az="Çiçəkləmə üçün fosfor təkanı",
        description="Apply phosphorus during flowering stage",
        description_az="Çiçəkləmə mərhələsində fosfor tətbiq edin",
        category="fertilization",
        farm_types=[FarmType.VEGETABLE, FarmType.ORCHARD],
        priority=TaskPriority.MEDIUM,
        condition=lambda soil, crop: (
            soil.phosphorus_level < 25 and
            crop.current_stage == CropStage.FLOWERING
        ),
        action_template="Apply phosphorus fertilizer to {crop} for better flowering",
        action_template_az="Daha yaxşı çiçəkləmə üçün {crop}-a fosfor gübrəsi tətbiq edin",
    ),
    Rule(
        id="FERT-003",
        name="Pre-Harvest Potassium",
        name_az="Məhsul yığımından əvvəl kalium",
        description="Apply potassium before harvest for better quality",
        description_az="Daha yaxşı keyfiyyət üçün məhsul yığımından əvvəl kalium tətbiq edin",
        category="fertilization",
        farm_types=[FarmType.VEGETABLE, FarmType.ORCHARD],
        priority=TaskPriority.MEDIUM,
        condition=lambda soil, crop: (
            soil.potassium_level < 100 and
            crop.current_stage in [CropStage.FRUITING, CropStage.MATURITY]
        ),
        action_template="Apply potassium to {crop} for improved fruit quality",
        action_template_az="Meyvə keyfiyyətini yaxşılaşdırmaq üçün {crop}-a kalium tətbiq edin",
    ),
    Rule(
        id="FERT-004",
        name="pH Adjustment",
        name_az="pH tənzimləməsi",
        description="Adjust soil pH when out of optimal range",
        description_az="Torpaq pH-ı optimal aralıqdan kənarda olduqda tənzimləyin",
        category="fertilization",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.LOW,
        condition=lambda soil, crop: (
            soil.ph_level < 5.5 or soil.ph_level > 7.5
        ),
        action_template="Adjust soil pH (current: {ph}) - apply {'lime' if soil.ph_level < 5.5 else 'sulfur'}",
        action_template_az="Torpaq pH-ını tənzimləyin (cari: {ph}) - {'əhəng' if soil.ph_level < 5.5 else 'kükürd'} tətbiq edin",
    ),
]


# ============= Pest & Disease Rules =============

PEST_DISEASE_RULES = [
    Rule(
        id="PEST-001",
        name="High Humidity Fungal Risk",
        name_az="Yüksək rütubət göbələk riski",
        description="Monitor for fungal diseases when humidity is high",
        description_az="Rütubət yüksək olduqda göbələk xəstəliklərini izləyin",
        category="pest_control",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.HIGH,
        condition=lambda weather, crop: (
            weather.humidity_percent > 75 and
            crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING, CropStage.FRUITING]
        ),
        action_template="Monitor {crop} for fungal diseases - humidity at {humidity}%",
        action_template_az="{crop}-ı göbələk xəstəlikləri üçün izləyin - rütubət {humidity}%",
    ),
    Rule(
        id="PEST-002",
        name="Aphid Alert - Warm & Dry",
        name_az="Mənənə xəbərdarlığı - isti və quru",
        description="Watch for aphids in warm, dry conditions",
        description_az="İsti, quru şəraitdə mənənələrə diqqət edin",
        category="pest_control",
        farm_types=[FarmType.VEGETABLE, FarmType.ORCHARD],
        priority=TaskPriority.MEDIUM,
        condition=lambda weather, crop: (
            weather.temperature_max > 25 and
            weather.humidity_percent < 50 and
            crop.current_stage in [CropStage.VEGETATIVE, CropStage.FLOWERING]
        ),
        action_template="Check {crop} for aphid infestation",
        action_template_az="{crop}-ı mənənə yoluxması üçün yoxlayın",
    ),
    Rule(
        id="PEST-003",
        name="Post-Rain Pest Inspection",
        name_az="Yağışdan sonra zərərverici müayinəsi",
        description="Inspect crops after heavy rain",
        description_az="Güclü yağışdan sonra bitkiləri yoxlayın",
        category="pest_control",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.MEDIUM,
        condition=lambda weather, crop: (
            weather.precipitation_mm > 15
        ),
        action_template="Inspect {crop} for pest/disease after {precipitation}mm rain",
        action_template_az="{precipitation}mm yağışdan sonra {crop}-ı zərərverici/xəstəlik üçün yoxlayın",
    ),
]


# ============= Harvest Rules =============

HARVEST_RULES = [
    Rule(
        id="HARV-001",
        name="Maturity Harvest Alert",
        name_az="Yetişmə məhsul yığımı xəbərdarlığı",
        description="Harvest when crop reaches maturity",
        description_az="Bitki yetişdikdə məhsul yığın",
        category="harvest",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.CRITICAL,
        condition=lambda weather, crop: (
            crop.current_stage == CropStage.MATURITY and
            weather.condition not in [WeatherCondition.RAINY, WeatherCondition.STORMY]
        ),
        action_template="Harvest {crop} - optimal conditions",
        action_template_az="{crop} məhsulunu yığın - optimal şərait",
    ),
    Rule(
        id="HARV-002",
        name="Pre-Storm Harvest Rush",
        name_az="Fırtınadan əvvəl təcili məhsul yığımı",
        description="Urgent harvest before storm",
        description_az="Fırtınadan əvvəl təcili məhsul yığımı",
        category="harvest",
        farm_types=[FarmType.WHEAT, FarmType.VEGETABLE, FarmType.ORCHARD, FarmType.MIXED],
        priority=TaskPriority.CRITICAL,
        condition=lambda weather, crop, forecast: (
            crop.current_stage in [CropStage.MATURITY, CropStage.HARVEST] and
            any(w.condition == WeatherCondition.STORMY for w in forecast)
        ),
        action_template="URGENT: Harvest {crop} before incoming storm",
        action_template_az="TƏCİLİ: Gələn fırtınadan əvvəl {crop} məhsulunu yığın",
    ),
]


# ============= Livestock Rules =============

LIVESTOCK_RULES = [
    Rule(
        id="LIVE-001",
        name="Heat Stress Prevention",
        name_az="İsti stresinin qarşısının alınması",
        description="Provide shade and water during extreme heat",
        description_az="Həddindən artıq istidə kölgə və su təmin edin",
        category="livestock",
        farm_types=[FarmType.LIVESTOCK, FarmType.MIXED],
        priority=TaskPriority.CRITICAL,
        condition=lambda weather, livestock: (
            weather.temperature_max > 32
        ),
        action_template="Ensure shade and extra water for {livestock_type}",
        action_template_az="{livestock_type} üçün kölgə və əlavə su təmin edin",
    ),
    Rule(
        id="LIVE-002",
        name="Vaccination Reminder",
        name_az="Peyvənd xatırlatması",
        description="Remind vaccination when overdue",
        description_az="Vaxtı keçdikdə peyvəndi xatırladın",
        category="livestock",
        farm_types=[FarmType.LIVESTOCK, FarmType.MIXED],
        priority=TaskPriority.HIGH,
        condition=lambda livestock, days_since_vaccination: (
            days_since_vaccination > 180
        ),
        action_template="Schedule vaccination for {livestock_type} - {days} days overdue",
        action_template_az="{livestock_type} üçün peyvənd planlaşdırın - {days} gün gecikib",
    ),
    Rule(
        id="LIVE-003",
        name="Cold Weather Shelter",
        name_az="Soyuq havada sığınacaq",
        description="Ensure proper shelter during cold weather",
        description_az="Soyuq havada düzgün sığınacaq təmin edin",
        category="livestock",
        farm_types=[FarmType.LIVESTOCK, FarmType.MIXED],
        priority=TaskPriority.HIGH,
        condition=lambda weather, livestock: (
            weather.temperature_min < 5
        ),
        action_template="Check shelter conditions for {livestock_type}",
        action_template_az="{livestock_type} üçün sığınacaq şəraitini yoxlayın",
    ),
    Rule(
        id="LIVE-004",
        name="Feeding Schedule Adjustment",
        name_az="Yemləmə cədvəlinin tənzimlənməsi",
        description="Adjust feeding based on weather",
        description_az="Hava şəraitinə görə yemləməni tənzimləyin",
        category="livestock",
        farm_types=[FarmType.LIVESTOCK, FarmType.MIXED],
        priority=TaskPriority.MEDIUM,
        condition=lambda weather, livestock: (
            weather.temperature_max > 30 or weather.temperature_min < 0
        ),
        action_template="Adjust feeding schedule for {livestock_type} due to weather",
        action_template_az="Hava şəraitinə görə {livestock_type} üçün yemləmə cədvəlini tənzimləyin",
    ),
]


# ============= Subsidy & Market Rules =============

SUBSIDY_RULES = [
    Rule(
        id="SUB-001",
        name="Subsidy Application Deadline",
        name_az="Subsidiya müraciət müddəti",
        description="Remind about upcoming subsidy deadlines",
        description_az="Gələn subsidiya müddətləri haqqında xatırlat",
        category="subsidy",
        farm_types=list(FarmType),
        priority=TaskPriority.HIGH,
        condition=lambda days_to_deadline: days_to_deadline <= 14,
        action_template="Subsidy deadline in {days} days - prepare documents",
        action_template_az="Subsidiya müddəti {days} gün sonra - sənədləri hazırlayın",
    ),
]


# ============= All Rules Collection =============

ALL_RULES = (
    IRRIGATION_RULES +
    FERTILIZATION_RULES +
    PEST_DISEASE_RULES +
    HARVEST_RULES +
    LIVESTOCK_RULES +
    SUBSIDY_RULES
)


def get_rules_by_category(category: str) -> list[Rule]:
    """Get all rules for a specific category."""
    return [r for r in ALL_RULES if r.category == category]


def get_rules_by_farm_type(farm_type: FarmType) -> list[Rule]:
    """Get all rules applicable to a farm type."""
    return [r for r in ALL_RULES if farm_type in r.farm_types]


def get_rule_by_id(rule_id: str) -> Optional[Rule]:
    """Get a specific rule by ID."""
    return next((r for r in ALL_RULES if r.id == rule_id), None)
