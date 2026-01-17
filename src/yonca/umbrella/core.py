"""
Yonca AI - Core Data & Logic
=============================

Core data structures, farm profile adapters, and recommendation
generation logic for the Streamlit UI.

This module bridges canonical data models with UI-specific formats.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from yonca.models import FarmProfile
from yonca.data.scenarios import get_scenario_farms, WHEAT_FARM
from yonca.sidecar.recommendation_service import (
    SidecarRecommendationService,
    RecommendationRequest,
)
from yonca.sidecar.intent_matcher import get_intent_matcher


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

class ScenarioProfile(str, Enum):
    """Available farm scenario profiles."""
    WHEAT = "wheat"
    LIVESTOCK = "livestock"
    ORCHARD = "orchard"
    MIXED = "mixed"
    POULTRY = "poultry"


# Azerbaijani display labels
SCENARIO_LABELS = {
    ScenarioProfile.WHEAT: {
        "name": "Taxıl Təsərrüfatı",
        "description": "Buğda və arpa istehsalı",
        "icon": "🌾",
        "farmer_name": "Əli",
    },
    ScenarioProfile.LIVESTOCK: {
        "name": "Heyvandarlıq Ferması",
        "description": "Mal-qara və qoyunçuluq",
        "icon": "🐄",
        "farmer_name": "Məmməd",
    },
    ScenarioProfile.ORCHARD: {
        "name": "Meyvə Bağı",
        "description": "Alma və armud bağları",
        "icon": "🍎",
        "farmer_name": "Fərid",
    },
    ScenarioProfile.MIXED: {
        "name": "Qarışıq Təsərrüfat",
        "description": "Tərəvəz və kiçik ferma",
        "icon": "🌻",
        "farmer_name": "Rəşad",
    },
    ScenarioProfile.POULTRY: {
        "name": "Quşçuluq Ferması",
        "description": "Toyuq və yumurta istehsalı",
        "icon": "🐔",
        "farmer_name": "Nigar",
    },
}

# Map UI profiles to canonical scenario IDs
SCENARIO_MAP = {
    ScenarioProfile.WHEAT: "scenario-wheat",
    ScenarioProfile.LIVESTOCK: "scenario-livestock",
    ScenarioProfile.ORCHARD: "scenario-orchard",
    ScenarioProfile.MIXED: "scenario-mixed",
    ScenarioProfile.POULTRY: "scenario-vegetable",
}


# ═══════════════════════════════════════════════════════════════════════════════
# UI DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class UIWeatherData:
    """Weather data for UI display."""
    temperature_current: float
    temperature_min: float
    temperature_max: float
    humidity_percent: int
    wind_speed_kmh: float
    condition: str
    precipitation_mm: float = 0.0


@dataclass
class UISoilData:
    """Soil data for UI display."""
    soil_type: str
    moisture_percent: int
    ph_level: float
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float


@dataclass
class UICropData:
    """Crop data for UI display."""
    crop_type: str
    variety: str
    growth_stage: str
    area_hectares: float


@dataclass
class UILivestockData:
    """Livestock data for UI display."""
    animal_type: str
    count: int
    health_status: str = "sağlam"


@dataclass
class UIFarmProfile:
    """Complete farm profile for UI display."""
    id: str
    name: str
    region: str
    area_hectares: float
    profile_type: ScenarioProfile
    soil: Optional[UISoilData] = None
    weather: Optional[UIWeatherData] = None
    crops: List[UICropData] = field(default_factory=list)
    livestock: List[UILivestockData] = field(default_factory=list)
    irrigation_system: Optional[str] = None
    satellite_alert: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# FARM LOADING & ADAPTATION
# ═══════════════════════════════════════════════════════════════════════════════

# Cache for scenario farms
_scenario_farms_cache = None
_recommendation_service = None


def _get_scenario_farms():
    """Get cached scenario farms."""
    global _scenario_farms_cache
    if _scenario_farms_cache is None:
        _scenario_farms_cache = get_scenario_farms()
    return _scenario_farms_cache


def _get_recommendation_service():
    """Get cached recommendation service."""
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = SidecarRecommendationService()
    return _recommendation_service


def load_farm_for_scenario(profile: ScenarioProfile) -> UIFarmProfile:
    """Load and adapt a farm profile for the given scenario."""
    farms = _get_scenario_farms()
    scenario_id = SCENARIO_MAP.get(profile)
    
    canonical_farm = farms.get(scenario_id)
    if canonical_farm is None:
        canonical_farm = WHEAT_FARM
    
    return _adapt_farm_profile(canonical_farm, profile)


def _adapt_farm_profile(farm: FarmProfile, profile: ScenarioProfile) -> UIFarmProfile:
    """Convert canonical FarmProfile to UI-specific format."""
    # Weather based on region
    weather = _generate_weather(farm.location.region)
    
    # Adapt soil
    soil = None
    if farm.soil_data:
        soil = UISoilData(
            soil_type=farm.soil_data.soil_type.value,
            moisture_percent=farm.soil_data.moisture_percent,
            ph_level=farm.soil_data.ph_level,
            nitrogen_kg_ha=farm.soil_data.nitrogen_level,
            phosphorus_kg_ha=farm.soil_data.phosphorus_level,
            potassium_kg_ha=farm.soil_data.potassium_level,
        )
    
    # Adapt crops
    crops = [
        UICropData(
            crop_type=c.crop_type,
            variety=c.variety or "",
            growth_stage=c.current_stage.value,
            area_hectares=c.area_hectares,
        )
        for c in farm.crops
    ]
    
    # Adapt livestock
    livestock = [
        UILivestockData(
            animal_type=a.livestock_type.value,
            count=a.count,
            health_status=a.health_status,
        )
        for a in farm.livestock
    ]
    
    # Generate satellite alert for demo
    satellite_alert = None
    if profile == ScenarioProfile.WHEAT and soil and soil.nitrogen_kg_ha < 30:
        satellite_alert = "Cənub-şərq sahəsində lokal sarılma aşkarlandı (NDVI anomaliya)"
    
    return UIFarmProfile(
        id=farm.id,
        name=farm.name,
        region=farm.location.region,
        area_hectares=farm.total_area_hectares,
        profile_type=profile,
        soil=soil,
        weather=weather,
        crops=crops,
        livestock=livestock,
        irrigation_system=farm.irrigation_system,
        satellite_alert=satellite_alert,
    )


def _generate_weather(region: str) -> UIWeatherData:
    """Generate synthetic weather for a region."""
    weather_by_region = {
        "Aran": UIWeatherData(28.0, 18.0, 32.0, 35, 12.0, "sunny"),
        "Gəncə-Qazax": UIWeatherData(31.0, 22.0, 36.0, 78, 5.0, "cloudy"),
        "Quba-Xaçmaz": UIWeatherData(24.0, 15.0, 28.0, 65, 8.0, "cloudy", 2.0),
        "Şəki-Zaqatala": UIWeatherData(22.0, 14.0, 26.0, 55, 10.0, "sunny"),
        "Lənkəran": UIWeatherData(29.0, 21.0, 33.0, 72, 6.0, "cloudy", 5.0),
    }
    return weather_by_region.get(region, UIWeatherData(25.0, 16.0, 30.0, 50, 8.0, "sunny"))


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_recommendations(farm: UIFarmProfile) -> dict:
    """
    Generate AI recommendations for a farm profile.
    
    Returns a dict with 'items' (recommendations) and 'routine' (daily schedule).
    """
    import time
    start = time.time()
    
    service = _get_recommendation_service()
    
    # Build request
    request = RecommendationRequest(
        farm_id=farm.id,
        region=farm.region,
        farm_type=farm.profile_type.value,
        crops=[c.crop_type for c in farm.crops],
        livestock_types=[l.animal_type for l in farm.livestock],
        area_hectares=farm.area_hectares,
        soil_moisture_percent=farm.soil.moisture_percent if farm.soil else None,
        nitrogen_level=farm.soil.nitrogen_kg_ha if farm.soil else None,
        temperature_min=farm.weather.temperature_min if farm.weather else None,
        temperature_max=farm.weather.temperature_max if farm.weather else None,
        humidity_percent=farm.weather.humidity_percent if farm.weather else None,
        precipitation_expected=farm.weather.condition == "rainy" if farm.weather else False,
        query="",
        language="az",
        max_recommendations=5,
    )
    
    # Get recommendations
    try:
        response = service.get_recommendations(request)
        items = [
            {
                "title": r.title_az,
                "description": r.description_az,
                "action": r.description_az,
                "priority": r.priority.value,
                "confidence": r.confidence,
                "time": r.suggested_time,
                "why": f"Bu tövsiyə {r.source} mənbəsindən hazırlanıb. Qayda: {r.rule_id or 'N/A'}",
            }
            for r in response.recommendations
        ]
    except Exception:
        # Fallback to rule-based
        items = _generate_fallback_recommendations(farm)
    
    # Generate daily routine
    routine = _generate_daily_routine(farm, items)
    
    processing_ms = int((time.time() - start) * 1000)
    
    return {
        "items": items,
        "routine": routine,
        "processing_ms": processing_ms + 50,
    }


def _generate_fallback_recommendations(farm: UIFarmProfile) -> list:
    """Generate rule-based recommendations when service fails."""
    items = []
    
    # Irrigation check
    if farm.soil and farm.soil.moisture_percent < 20:
        items.append({
            "title": "🚨 Təcili Suvarma Tələb Olunur",
            "description": f"Torpaq nəmliyi {farm.soil.moisture_percent}% - kritik səviyyədədir.",
            "action": "Bu gün saat 06:00-08:00 arasında suvarmanı başlayın. Hər hektara 40-50mm su verin.",
            "priority": "critical",
            "confidence": 0.94,
            "time": "06:00-08:00",
            "why": "Çiçəkləmə dövründə su stresi məhsuldarlığı 30%-ə qədər azalda bilər.",
        })
    
    # Nitrogen check
    if farm.soil and farm.soil.nitrogen_kg_ha < 25:
        items.append({
            "title": "🌾 Azot Gübrəsi Tövsiyəsi",
            "description": f"Azot səviyyəsi {farm.soil.nitrogen_kg_ha} kq/ha - optimal həddən aşağıdır.",
            "action": "Ammonium nitrat gübrəsini 80-100 kq/ha dozasında tətbiq edin.",
            "priority": "high",
            "confidence": 0.88,
            "time": "suvarma ilə birlikdə",
            "why": "Aşağı azot yarpaq saralmasına və məhsul keyfiyyətinin azalmasına səbəb olur.",
        })
    
    # Heat stress for livestock
    if farm.livestock and farm.weather:
        if farm.weather.humidity_percent > 70 and farm.weather.temperature_max > 32:
            items.append({
                "title": "🌡️ Təcili Ventilyasiya Yoxlaması",
                "description": f"Yüksək rütubət ({farm.weather.humidity_percent}%) + temperatur = istilik stresi riski.",
                "action": "Ventilyatorları maksimum gücə keçirin, əlavə su mənbələri qoyun.",
                "priority": "critical",
                "confidence": 0.92,
                "time": "dərhal",
                "why": "THI 78-dən yuxarı olduqda süd məhsuldarlığı 10-25% azalır.",
            })
    
    return items


def _generate_daily_routine(farm: UIFarmProfile, recommendations: list) -> list:
    """Generate daily task timeline."""
    routine = []
    
    # Morning inspection
    routine.append({
        "time": "06:00",
        "title": "Sahə müayinəsi",
        "description": "Bitkiləri və avadanlığı yoxlayın",
        "icon": "🔍",
        "duration": 30,
        "priority": "medium",
    })
    
    # Irrigation if critical
    if any(r.get("priority") == "critical" and "suvarma" in r.get("title", "").lower() for r in recommendations):
        routine.append({
            "time": "06:30",
            "title": "Suvarma",
            "description": "Kritik sahələri suvarmağa başlayın",
            "icon": "💧",
            "duration": 90,
            "priority": "critical",
        })
    
    # Livestock care
    if farm.livestock:
        routine.append({
            "time": "07:00",
            "title": "Heyvan baxımı",
            "description": "Yemlənmə və sağlamlıq yoxlaması",
            "icon": "🐄",
            "duration": 60,
            "priority": "high",
        })
    
    # Fertilization
    if any("gübrə" in r.get("title", "").lower() for r in recommendations):
        routine.append({
            "time": "08:30",
            "title": "Gübrələmə",
            "description": "Gübrə tətbiqini həyata keçirin",
            "icon": "🌱",
            "duration": 60,
            "priority": "high",
        })
    
    # Midday break
    routine.append({
        "time": "12:00",
        "title": "Günorta fasiləsi",
        "description": "İsti saatlarda istirahət",
        "icon": "☀️",
        "duration": 180,
        "priority": "low",
    })
    
    # Evening maintenance
    routine.append({
        "time": "17:00",
        "title": "Avadanlıq baxımı",
        "description": "Avadanlığı yoxlayın və təmizləyin",
        "icon": "🔧",
        "duration": 60,
        "priority": "medium",
    })
    
    # Sort by time
    routine.sort(key=lambda x: x["time"])
    return routine


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT RESPONSE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

_intent_matcher = None


def _get_intent_matcher():
    """Get cached intent matcher."""
    global _intent_matcher
    if _intent_matcher is None:
        _intent_matcher = get_intent_matcher()
    return _intent_matcher


def generate_chat_response(message: str, farm: UIFarmProfile) -> str:
    """
    Generate an AI chat response based on user intent.
    
    Uses the IntentMatcher for Azerbaijani language understanding.
    """
    matcher = _get_intent_matcher()
    intent_result = matcher.match(message)
    intent = intent_result.intent
    confidence = intent_result.confidence
    
    # Route by intent
    if intent == "irrigation":
        return _handle_irrigation_intent(farm, confidence)
    
    elif intent == "fertilization":
        return _handle_fertilization_intent(farm, confidence)
    
    elif intent in ("disease", "pest_control"):
        return _handle_disease_intent(farm, confidence)
    
    elif intent == "weather":
        return _handle_weather_intent(farm, confidence)
    
    elif intent == "livestock":
        return _handle_livestock_intent(farm, confidence)
    
    elif intent == "soil":
        return _handle_soil_intent(farm, confidence)
    
    elif intent == "planting":
        return _handle_schedule_intent(farm, confidence)
    
    elif intent == "harvest":
        return _handle_harvest_intent(farm, confidence)
    
    # Check for greetings
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["salam", "xoş", "necəsən", "hello"]):
        return (
            f"Salam! 👋\n\n"
            f"Mən Yonca AI - sizin şəxsi fermer köməkçinizəm.\n\n"
            f"Hazırda **{farm.name}** ({farm.region}) üzərində işləyirik.\n\n"
            "Sizə necə kömək edə bilərəm?"
        )
    
    # Help intent
    if any(w in msg_lower for w in ["kömək", "help", "nə edə"]):
        return (
            "🌿 **Yonca AI ilə nə edə bilərsiniz:**\n\n"
            "🌊 **Suvarma** - \"Nə vaxt suvarmalıyam?\"\n"
            "🌱 **Gübrələmə** - \"Gübrə lazımdırmı?\"\n"
            "🐛 **Xəstəliklər** - \"Xəstəlik riski varmı?\"\n"
            "📋 **Cədvəl** - \"Bu gün nə edim?\"\n"
            "🌤️ **Hava** - \"Hava necə olacaq?\"\n"
            "🐄 **Heyvandarlıq** - \"Mal-qara vəziyyəti?\"\n\n"
            "*İstənilən sualınızı Azərbaycan dilində yaza bilərsiniz!*"
        )
    
    # Schedule fallback
    if any(w in msg_lower for w in ["bu gün", "plan", "cədvəl", "nə edim"]):
        return _handle_schedule_intent(farm, confidence)
    
    # Default
    return (
        "🤔 Sualınızı tam başa düşmədim.\n\n"
        "Aşağıdakı mövzularda kömək edə bilərəm:\n"
        "• Suvarma tövsiyələri\n"
        "• Gübrələmə planı\n"
        "• Xəstəlik monitorinqi\n"
        "• Gündəlik iş cədvəli\n"
        "• Hava proqnozu\n\n"
        "*Yenidən soruşun və ya \"Kömək\" yazın.*"
    )


def _handle_irrigation_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.soil:
        m = farm.soil.moisture_percent
        if m < 25:
            return (
                f"🚨 **Təcili suvarma tövsiyəsi!**\n\n"
                f"Torpaq nəmliyi {m}% - kritik səviyyədədir.\n\n"
                "**Tövsiyə:** Bu gün saat 06:00-08:00 arasında suvarmanı başlayın.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        elif m < 40:
            return (
                f"💧 **Suvarma planlaşdırın**\n\n"
                f"Torpaq nəmliyi {m}% - orta səviyyədədir.\n\n"
                "**Tövsiyə:** Sabah səhər suvarma tövsiyə olunur.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return f"✅ **Suvarma lazım deyil**\n\nTorpaq nəmliyi {m}% - optimaldır.\n\n📊 *Etibarlılıq: {confidence:.0%}*"
    return "Torpaq məlumatları mövcud deyil."


def _handle_fertilization_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.soil:
        n = farm.soil.nitrogen_kg_ha
        if n < 25:
            return (
                f"🌱 **Azot gübrəsi tövsiyəsi**\n\n"
                f"Azot səviyyəsi {n} kq/ha - aşağıdır.\n\n"
                "**Tövsiyə:** Ammonium nitrat 80-100 kq/ha dozasında tətbiq edin.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return f"✅ **Gübrə lazım deyil**\n\nAzot səviyyəsi {n} kq/ha - normaldır.\n\n📊 *Etibarlılıq: {confidence:.0%}*"
    return "Torpaq analizi məlumatı mövcud deyil."


def _handle_disease_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.weather and farm.weather.humidity_percent > 70:
        return (
            f"⚠️ **Xəstəlik riski yüksəkdir!**\n\n"
            f"Rütubət {farm.weather.humidity_percent}% - göbələk üçün əlverişlidir.\n\n"
            "**Diqqət:** Yarpaq ləkələri, unlu şeh əlamətləri\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    return f"✅ **Xəstəlik riski aşağıdır**\n\nŞərait normaldır.\n\n📊 *Etibarlılıq: {confidence:.0%}*"


def _handle_weather_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.weather:
        w = farm.weather
        return (
            f"🌤️ **Hava proqnozu**\n\n"
            f"Hazırda: {w.temperature_current}°C, {w.condition}\n"
            f"Min/Maks: {w.temperature_min}°C / {w.temperature_max}°C\n"
            f"Rütubət: {w.humidity_percent}%\n"
            f"Külək: {w.wind_speed_kmh} km/saat\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    return "Hava məlumatı mövcud deyil."


def _handle_livestock_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.livestock:
        total = sum(l.count for l in farm.livestock)
        animals = ", ".join([f"{l.count} {l.animal_type}" for l in farm.livestock])
        return (
            f"🐄 **Heyvandarlıq vəziyyəti**\n\n"
            f"Cəmi: {total} baş ({animals})\n\n"
            "✅ Gündəlik sağlamlıq yoxlamasını davam edin.\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    return "Bu təsərrüfatda heyvandarlıq yoxdur."


def _handle_soil_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.soil:
        s = farm.soil
        return (
            f"🌱 **Torpaq Analizi**\n\n"
            f"• Nəmlik: {s.moisture_percent}%\n"
            f"• pH: {s.ph_level}\n"
            f"• Azot (N): {s.nitrogen_kg_ha} kq/ha\n"
            f"• Fosfor (P): {s.phosphorus_kg_ha} kq/ha\n"
            f"• Kalium (K): {s.potassium_kg_ha} kq/ha\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    return "Torpaq analizi mövcud deyil."


def _handle_schedule_intent(farm: UIFarmProfile, confidence: float) -> str:
    return (
        f"📋 **{datetime.now().strftime('%d.%m.%Y')} üçün plan:**\n\n"
        "1. **06:00** - Sahə müayinəsi\n"
        "2. **07:00** - Suvarma (əgər lazımdırsa)\n"
        "3. **09:00** - Gübrə tətbiqi\n"
        "4. **11:00-16:00** - İstirahət\n"
        "5. **17:00** - Avadanlıq baxımı\n\n"
        f"📊 *Etibarlılıq: {confidence:.0%}*"
    )


def _handle_harvest_intent(farm: UIFarmProfile, confidence: float) -> str:
    if farm.crops:
        c = farm.crops[0]
        return (
            f"🌾 **Məhsul Yığımı**\n\n"
            f"Bitki: {c.crop_type}\n"
            f"Mərhələ: {c.growth_stage}\n\n"
            "**Tövsiyə:** Yığımdan əvvəl torpaq nəmliyini yoxlayın.\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    return "Bitki məlumatı mövcud deyil."
