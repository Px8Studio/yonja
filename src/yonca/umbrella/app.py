"""
Yonca AI - Digital Umbrella Streamlit App
==========================================

Mobile-first "Personalized Farm Assistant" prototype.
Primary language: Azerbaijani (az)

Usage:
    streamlit run src/yonca/umbrella/app.py

Features:
    1. Scenario Switcher - Toggle between 5 farm profiles
    2. Profile Overview - Synthetic data display
    3. AI Advisory - Core value proposition with insight cards
    4. Simple Chat - Intent-based Azerbaijani chatbot

Architecture Note:
    This app consumes the Sidecar Intelligence Engine for recommendations.
    Farm scenarios are loaded from the canonical yonca.data.scenarios module.
"""

import streamlit as st
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass

# Canonical data models and scenarios
from yonca.models import FarmProfile
from yonca.data.scenarios import get_scenario_farms, WHEAT_FARM

# Sidecar Intelligence Engine
from yonca.sidecar.recommendation_service import (
    SidecarRecommendationService,
    RecommendationRequest,
    RecommendationResponse,
)
from yonca.sidecar.intent_matcher import get_intent_matcher, IntentMatch

# UI Styles
from yonca.umbrella.styles import (
    get_all_styles,
    render_header,
    render_insight_card,
    render_chat_bubble,
    render_timeline_item,
    render_profile_card,
    COLORS,
)


# ============= UI SCENARIO PROFILES =============

class ScenarioProfile(str, Enum):
    """Available farm scenario profiles for UI."""
    WHEAT = "wheat"
    LIVESTOCK = "livestock"
    ORCHARD = "orchard"
    MIXED = "mixed"
    POULTRY = "poultry"


# Azerbaijani labels for UI display
SCENARIO_LABELS = {
    ScenarioProfile.WHEAT: {
        "name": "Taxıl Təsərrüfatı",
        "description": "Buğda və arpa istehsalı",
        "icon": "🌾",
        "region": "Aran",
    },
    ScenarioProfile.LIVESTOCK: {
        "name": "Heyvandarlıq Ferması",
        "description": "Mal-qara və qoyunçuluq",
        "icon": "🐄",
        "region": "Gəncə-Qazax",
    },
    ScenarioProfile.ORCHARD: {
        "name": "Meyvə Bağı",
        "description": "Alma və armud bağları",
        "icon": "🍎",
        "region": "Quba-Xaçmaz",
    },
    ScenarioProfile.MIXED: {
        "name": "Qarışıq Təsərrüfat",
        "description": "Tərəvəz və kiçik ferma",
        "icon": "🌻",
        "region": "Şəki-Zaqatala",
    },
    ScenarioProfile.POULTRY: {
        "name": "Quşçuluq Ferması",
        "description": "Toyuq və yumurta istehsalı",
        "icon": "🐔",
        "region": "Lənkəran",
    },
}

# Map UI profiles to canonical scenario IDs
SCENARIO_MAP = {
    ScenarioProfile.WHEAT: "scenario-wheat",
    ScenarioProfile.LIVESTOCK: "scenario-livestock",
    ScenarioProfile.ORCHARD: "scenario-orchard",
    ScenarioProfile.MIXED: "scenario-mixed",
    ScenarioProfile.POULTRY: "scenario-vegetable",  # Use vegetable as poultry demo
}


# ============= UI DATA ADAPTERS =============

@dataclass
class UIWeatherData:
    """Weather data adapted for UI display."""
    temperature_current: float
    temperature_min: float
    temperature_max: float
    humidity_percent: int
    wind_speed_kmh: float
    condition: str
    precipitation_mm: float = 0.0
    uv_index: int = 5


@dataclass
class UISoilData:
    """Soil data adapted for UI display."""
    soil_type: str
    moisture_percent: int
    ph_level: float
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float


@dataclass
class UICropData:
    """Crop data adapted for UI display."""
    crop_type: str
    variety: str
    growth_stage: str
    area_hectares: float
    health_status: str = "healthy"


@dataclass
class UILivestockData:
    """Livestock data adapted for UI display."""
    animal_type: str
    count: int
    health_status: str = "sağlam"
    housing_condition: str = "good"


@dataclass
class UIFarmProfile:
    """Farm profile adapted for UI display with all needed fields."""
    id: str
    profile_type: ScenarioProfile
    name: str
    region: str
    area_hectares: float
    soil: Optional[UISoilData] = None
    weather: Optional[UIWeatherData] = None
    crops: Optional[list] = None
    livestock: Optional[list] = None
    irrigation_system: Optional[str] = None
    satellite_alert: Optional[str] = None
    
    def __post_init__(self):
        if self.crops is None:
            self.crops = []
        if self.livestock is None:
            self.livestock = []


def adapt_farm_profile(farm: FarmProfile, profile_type: ScenarioProfile) -> UIFarmProfile:
    """Convert canonical FarmProfile to UI-specific format with synthetic weather."""
    # Generate synthetic weather based on region
    weather = _generate_weather_for_region(farm.location.region)
    
    # Convert soil data
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
    
    # Convert crops
    crops = []
    for crop in farm.crops:
        crops.append(UICropData(
            crop_type=crop.crop_type,
            variety=crop.variety or "",
            growth_stage=crop.current_stage.value,
            area_hectares=crop.area_hectares,
            health_status="stressed" if soil and soil.moisture_percent < 20 else "healthy",
        ))
    
    # Convert livestock
    livestock = []
    for animal in farm.livestock:
        livestock.append(UILivestockData(
            animal_type=animal.livestock_type.value,
            count=animal.count,
            health_status=animal.health_status,
            housing_condition="good",
        ))
    
    # Generate satellite alert for wheat scenario
    satellite_alert = None
    if profile_type == ScenarioProfile.WHEAT and soil and soil.nitrogen_kg_ha < 30:
        satellite_alert = "Cənub-şərq sahəsində lokal sarılma aşkarlandı (NDVI anomaliya)"
    
    return UIFarmProfile(
        id=farm.id,
        profile_type=profile_type,
        name=farm.name,
        region=farm.location.region,
        area_hectares=farm.total_area_hectares,
        soil=soil,
        weather=weather,
        crops=crops,
        livestock=livestock,
        irrigation_system=farm.irrigation_system,
        satellite_alert=satellite_alert,
    )


def _generate_weather_for_region(region: str) -> UIWeatherData:
    """Generate synthetic weather data based on region."""
    weather_profiles = {
        "Aran": UIWeatherData(28.0, 18.0, 32.0, 35, 12.0, "sunny"),
        "Gəncə-Qazax": UIWeatherData(31.0, 22.0, 36.0, 78, 5.0, "cloudy"),
        "Quba-Xaçmaz": UIWeatherData(24.0, 15.0, 28.0, 65, 8.0, "cloudy", 2.0),
        "Şəki-Zaqatala": UIWeatherData(22.0, 14.0, 26.0, 55, 10.0, "sunny"),
        "Lənkəran": UIWeatherData(29.0, 21.0, 33.0, 72, 6.0, "cloudy", 5.0),
    }
    return weather_profiles.get(region, UIWeatherData(25.0, 16.0, 30.0, 50, 8.0, "sunny"))


# ============= RECOMMENDATION ADAPTER =============

@dataclass
class UIRecommendation:
    """Recommendation adapted for UI display."""
    id: str
    type: str
    priority: str
    confidence: float
    title: str
    description: str
    action: str
    why_title: str
    why_explanation: str
    rule_id: Optional[str] = None
    source: str = "hybrid"
    suggested_time: Optional[str] = None


@dataclass
class UIDailyRoutineItem:
    """Daily routine item for timeline display."""
    time_slot: str
    duration_minutes: int
    title: str
    description: str
    icon: str
    category: str
    priority: str


@dataclass
class UIRecommendationPayload:
    """Complete recommendation payload for UI."""
    request_id: str
    farm_id: str
    recommendations: list
    daily_routine: list
    critical_count: int
    total_count: int
    processing_time_ms: int
    inference_engine: str = "qwen2.5-7b"


def generate_ui_recommendations(farm: UIFarmProfile, service: SidecarRecommendationService) -> UIRecommendationPayload:
    """Generate recommendations using sidecar service and adapt for UI."""
    import time
    start = time.time()
    
    # Build request from UI farm profile
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
    
    # Get recommendations from sidecar service
    try:
        response = service.get_recommendations(request)
        recommendations = _adapt_recommendations(response, farm)
    except Exception:
        # Fallback to rule-based recommendations if service fails
        recommendations = _generate_rule_based_recommendations(farm)
    
    # Generate daily routine
    daily_routine = _generate_daily_routine(farm, recommendations)
    
    # Count critical recommendations
    critical_count = sum(1 for r in recommendations if r.priority == "critical")
    
    processing_time = int((time.time() - start) * 1000)
    
    return UIRecommendationPayload(
        request_id=f"req-{farm.id}-{int(time.time())}",
        farm_id=farm.id,
        recommendations=recommendations,
        daily_routine=daily_routine,
        critical_count=critical_count,
        total_count=len(recommendations),
        processing_time_ms=processing_time + 50,
        inference_engine="qwen2.5-7b",
    )


def _adapt_recommendations(response: RecommendationResponse, farm: UIFarmProfile) -> list:
    """Adapt sidecar recommendations to UI format."""
    ui_recs = []
    for rec in response.recommendations:
        ui_recs.append(UIRecommendation(
            id=rec.id,
            type=rec.type,
            priority=rec.priority.value,
            confidence=rec.confidence,
            title=rec.title_az,
            description=rec.description_az,
            action=rec.description_az,  # Use description as action
            why_title="Niyə bu tövsiyə?",
            why_explanation=f"Bu tövsiyə {rec.source} mənbəsindən hazırlanıb.",
            rule_id=rec.rule_id,
            source=rec.source,
            suggested_time=rec.suggested_time,
        ))
    return ui_recs


def _generate_rule_based_recommendations(farm: UIFarmProfile) -> list:
    """Generate recommendations from rules registry when service unavailable."""
    recommendations = []
    
    # Check irrigation needs
    if farm.soil and farm.soil.moisture_percent < 20:
        recommendations.append(UIRecommendation(
            id=f"rec-irr-{farm.id}",
            type="irrigation",
            priority="critical",
            confidence=0.94,
            title="🚨 Təcili Suvarma Tələb Olunur",
            description=f"Torpaq nəmliyi {farm.soil.moisture_percent}% - kritik səviyyədədir.",
            action="Bu gün saat 06:00-08:00 arasında suvarmanı başlayın. Hər hektara 40-50mm su verin.",
            why_title="Niyə bu tövsiyə?",
            why_explanation="Çiçəkləmə mərhələsində torpaq nəmliyi 30%-dən aşağı düşdükdə, məhsuldarlıq 20-40% azala bilər.",
            rule_id="AZ-IRR-001",
            source="rulebook",
            suggested_time="06:00-08:00",
        ))
    
    # Check nitrogen levels
    if farm.soil and farm.soil.nitrogen_kg_ha < 25:
        recommendations.append(UIRecommendation(
            id=f"rec-fert-{farm.id}",
            type="fertilization",
            priority="high",
            confidence=0.88,
            title="🌾 Azot Gübrəsi Tövsiyəsi",
            description=f"Azot səviyyəsi {farm.soil.nitrogen_kg_ha} kq/ha - optimal həddən aşağıdır.",
            action="Ammonium nitrat gübrəsini 80-100 kq/ha dozasında tətbiq edin.",
            why_title="Niyə azot gübrəsi?",
            why_explanation="Aşağı azot səviyyəsi yarpaq saralmasına və məhsul keyfiyyətinin azalmasına səbəb olur.",
            rule_id="AZ-FERT-003",
            source="rulebook",
            suggested_time="suvarma ilə birlikdə",
        ))
    
    # Check heat stress for livestock
    if farm.livestock and farm.weather:
        if farm.weather.humidity_percent > 70 and farm.weather.temperature_max > 32:
            recommendations.append(UIRecommendation(
                id=f"rec-vent-{farm.id}",
                type="ventilation",
                priority="critical",
                confidence=0.92,
                title="🌡️ Təcili Ventilyasiya Yoxlaması",
                description=f"Yüksək rütubət ({farm.weather.humidity_percent}%) + temperatur ({farm.weather.temperature_max}°C) = istilik stresi riski.",
                action="Ventilyatorları maksimum gücə keçirin, əlavə su mənbələri qoyun.",
                why_title="İstilik stresi nədir?",
                why_explanation="THI 78-dən yuxarı olduqda mal-qara istilik stressinə məruz qalır, süd məhsuldarlığı 10-25% azalır.",
                rule_id="AZ-LIVE-002",
                source="rulebook",
                suggested_time="dərhal",
            ))
    
    return recommendations


def _generate_daily_routine(farm: UIFarmProfile, recommendations: list) -> list:
    """Generate daily routine timeline based on farm type and recommendations."""
    routine = []
    
    # Morning inspection
    routine.append(UIDailyRoutineItem(
        time_slot="06:00",
        duration_minutes=30,
        title="Sahə müayinəsi",
        description="Bitkiləri və avadanlığı yoxlayın",
        icon="🔍",
        category="inspection",
        priority="medium",
    ))
    
    # Add irrigation if needed
    if any(r.type == "irrigation" for r in recommendations):
        routine.append(UIDailyRoutineItem(
            time_slot="06:30",
            duration_minutes=90,
            title="Suvarma",
            description="Kritik sahələri suvarmağa başlayın",
            icon="💧",
            category="irrigation",
            priority="critical",
        ))
    
    # Fertilization
    if any(r.type == "fertilization" for r in recommendations):
        routine.append(UIDailyRoutineItem(
            time_slot="08:30",
            duration_minutes=60,
            title="Gübrələmə",
            description="Gübrə tətbiqini həyata keçirin",
            icon="🌱",
            category="fertilization",
            priority="high",
        ))
    
    # Livestock care
    if farm.livestock:
        routine.append(UIDailyRoutineItem(
            time_slot="07:00",
            duration_minutes=60,
            title="Heyvan baxımı",
            description="Yemlənmə və sağlamlıq yoxlaması",
            icon="🐄",
            category="livestock",
            priority="high",
        ))
    
    # Midday break
    routine.append(UIDailyRoutineItem(
        time_slot="12:00",
        duration_minutes=180,
        title="Günorta fasiləsi",
        description="İsti saatlarda istirahət",
        icon="☀️",
        category="break",
        priority="low",
    ))
    
    # Evening tasks
    routine.append(UIDailyRoutineItem(
        time_slot="17:00",
        duration_minutes=60,
        title="Avadanlıq baxımı",
        description="Avadanlığı yoxlayın və təmizləyin",
        icon="🔧",
        category="maintenance",
        priority="medium",
    ))
    
    # Sort by time
    routine.sort(key=lambda x: x.time_slot)
    
    return routine


# ============= PAGE CONFIG =============

st.set_page_config(
    page_title="Yonca AI - Fermer Köməkçisi",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============= SESSION STATE INITIALIZATION =============

def init_session_state():
    """Initialize session state variables."""
    if "scenario_farms" not in st.session_state:
        # Load canonical scenarios from data module
        st.session_state.scenario_farms = get_scenario_farms()
    
    if "recommendation_service" not in st.session_state:
        # Initialize sidecar recommendation service
        st.session_state.recommendation_service = SidecarRecommendationService()
    
    if "current_profile" not in st.session_state:
        st.session_state.current_profile = ScenarioProfile.WHEAT
    
    if "current_farm" not in st.session_state:
        # Get initial farm from canonical scenarios
        scenario_id = SCENARIO_MAP[ScenarioProfile.WHEAT]
        canonical_farm = st.session_state.scenario_farms.get(scenario_id)
        if canonical_farm:
            st.session_state.current_farm = adapt_farm_profile(canonical_farm, ScenarioProfile.WHEAT)
        else:
            # Fallback to wheat farm directly
            st.session_state.current_farm = adapt_farm_profile(WHEAT_FARM, ScenarioProfile.WHEAT)
    
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "tövsiyələr"
    
    if "request_counter" not in st.session_state:
        st.session_state.request_counter = 0


init_session_state()


# ============= INTENT-BASED CHAT RESPONSE (Unified) =============

# Get the singleton intent matcher
_intent_matcher = get_intent_matcher()


def generate_chat_response(user_message: str, farm) -> str:
    """
    Generate an intent-based response in Azerbaijani.
    
    Uses the unified IntentMatcher from sidecar module for
    dialect-aware, pattern-based intent detection.
    
    This simulates Qwen2.5-7B inference for demo purposes.
    """
    # Use unified intent matcher
    intent_result: IntentMatch = _intent_matcher.match(user_message)
    intent = intent_result.intent
    confidence = intent_result.confidence
    
    # Log for debugging (visible in console)
    # print(f"[Intent] {intent} ({confidence:.0%}) - patterns: {intent_result.matched_patterns}")
    
    # Route to appropriate handler based on detected intent
    if intent == "irrigation":
        if farm.soil:
            moisture = farm.soil.moisture_percent
            if moisture < 25:
                return (
                    f"🚨 **Təcili suvarma tövsiyəsi!**\n\n"
                    f"Torpaq nəmliyi {moisture}% - kritik səviyyədədir.\n\n"
                    "**Tövsiyə:** Bu gün saat 06:00-08:00 arasında suvarmanı başlayın. "
                    "Hər hektara 40-50mm su verin.\n\n"
                    "❓ *Niyə?* Çiçəkləmə dövründə su stresi məhsuldarlığı 30%-ə qədər azalda bilər.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            elif moisture < 40:
                return (
                    f"💧 **Suvarma planlaşdırın**\n\n"
                    f"Torpaq nəmliyi {moisture}% - orta səviyyədədir.\n\n"
                    "**Tövsiyə:** Sabah səhər suvarma tövsiyə olunur. "
                    "Damcı suvarma sistemindən istifadə edin.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            else:
                return (
                    f"✅ **Suvarma lazım deyil**\n\n"
                    f"Torpaq nəmliyi {moisture}% - optimal səviyyədədir.\n\n"
                    "Növbəti yoxlama 2 gün sonra.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
        return "Torpaq məlumatları mövcud deyil. Əvvəlcə nəmlik ölçmə aparın."
    
    # Fertilization intent
    elif intent == "fertilization":
        if farm.soil:
            nitrogen = farm.soil.nitrogen_kg_ha
            if nitrogen < 25:
                return (
                    f"🌱 **Azot gübrəsi tövsiyəsi**\n\n"
                    f"Azot səviyyəsi {nitrogen} kq/ha - aşağıdır.\n\n"
                    "**Tövsiyə:** Ammonium nitrat (NH₄NO₃) gübrəsini 80-100 kq/ha dozasında tətbiq edin.\n\n"
                    "⏰ *Ən yaxşı vaxt:* Səhər suvarması ilə birlikdə\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            else:
                return (
                    f"✅ **Gübrə hazırda lazım deyil**\n\n"
                    f"Azot səviyyəsi {nitrogen} kq/ha - normal həddədədir.\n\n"
                    "2 həftə sonra yenidən yoxlayın.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
        return "Torpaq analizi məlumatı mövcud deyil."
    
    # Disease/pest intent (matches both "disease" and "pest_control" from intent matcher)
    elif intent in ("disease", "pest_control"):
        if farm.weather and farm.weather.humidity_percent > 70:
            return (
                f"⚠️ **Xəstəlik riski yüksəkdir!**\n\n"
                f"Hazırkı rütubət {farm.weather.humidity_percent}% - göbələk xəstəlikləri üçün əlverişlidir.\n\n"
                "**Diqqət edin:**\n"
                "• Yarpaq ləkələri\n"
                "• Unlu şeh əlamətləri\n"
                "• Gövdə çürüməsi\n\n"
                "**Tövsiyə:** Fungisid tətbiqi planlaşdırın.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return (
            "✅ **Xəstəlik riski aşağıdır**\n\n"
            "Hazırkı şərait normal həddədədir. Həftəlik vizual müayinə davam edin.\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    
    # Planting intent (for schedule questions)
    elif intent == "planting":
        return (
            f"📋 **{datetime.now().strftime('%d.%m.%Y')} üçün plan:**\n\n"
            "1. **06:00** - Sahə müayinəsi\n"
            "2. **07:00** - Suvarma (əgər lazımdırsa)\n"
            "3. **09:00** - Gübrə tətbiqi\n"
            "4. **11:00-16:00** - İstirahət (günorta istisi)\n"
            "5. **17:00** - Avadanlıq baxımı\n\n"
            "📌 *\"Gündəlik Plan\" tabına baxın detallı cədvəl üçün.*\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    
    # Weather intent
    elif intent == "weather":
        if farm.weather:
            w = farm.weather
            rain_status = "🌧️ Yağış gözlənilir" if w.condition == "rainy" else "☀️ Quru hava"
            return (
                f"🌤️ **Hava proqnozu**\n\n"
                f"Hazırda: {w.temperature_current}°C, {w.condition}\n"
                f"Min/Maks: {w.temperature_min}°C / {w.temperature_max}°C\n"
                f"Rütubət: {w.humidity_percent}%\n"
                f"Külək: {w.wind_speed_kmh} km/saat\n\n"
                f"**Proqnoz:** {rain_status}\n\n"
                f"*Yağış planlarınızı suvarma cədvəlinə uyğunlaşdırın.*\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Hava məlumatı mövcud deyil."
    
    # Livestock intent
    elif intent == "livestock":
        if farm.livestock:
            total = sum(l.count for l in farm.livestock)
            animals = ", ".join([f"{l.count} {l.animal_type}" for l in farm.livestock])
            
            if farm.weather and farm.weather.humidity_percent > 70 and farm.weather.temperature_max > 30:
                return (
                    f"🐄 **Heyvandarlıq vəziyyəti**\n\n"
                    f"Cəmi: {total} baş ({animals})\n\n"
                    "⚠️ **DİQQƏT: İstilik stresi riski!**\n\n"
                    "• Ventilyasiya sistemini yoxlayın\n"
                    "• Əlavə su mənbələri təmin edin\n"
                    "• Günorta yemlənməni təxirə salın\n"
                    "• Respirator simptomlara diqqət edin\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            return (
                f"🐄 **Heyvandarlıq vəziyyəti**\n\n"
                f"Cəmi: {total} baş ({animals})\n\n"
                "✅ Şərait normaldır. Gündəlik sağlamlıq yoxlamasını davam edin.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Bu təsərrüfatda heyvandarlıq məlumatı yoxdur."
    
    # Soil intent
    elif intent == "soil":
        if farm.soil:
            return (
                f"🌱 **Torpaq Analizi**\n\n"
                f"• Nəmlik: {farm.soil.moisture_percent}%\n"
                f"• pH: {farm.soil.ph_level}\n"
                f"• Azot (N): {farm.soil.nitrogen_kg_ha} kq/ha\n"
                f"• Fosfor (P): {farm.soil.phosphorus_kg_ha} kq/ha\n"
                f"• Kalium (K): {farm.soil.potassium_kg_ha} kq/ha\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Torpaq analizi məlumatı mövcud deyil."
    
    # Harvest intent
    elif intent == "harvest":
        if farm.crops:
            crop = farm.crops[0]
            return (
                f"🌾 **Məhsul Yığımı**\n\n"
                f"Bitki: {crop.crop_type}\n"
                f"Mərhələ: {crop.growth_stage}\n\n"
                "**Tövsiyə:** Məhsul yığımından əvvəl torpaq nəmliyini yoxlayın.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Bitki məlumatı mövcud deyil."
    
    # Check for greeting patterns in the original message
    msg_lower = user_message.lower()
    if any(word in msg_lower for word in ["salam", "xoş", "necəsən", "hello", "hi"]):
        return (
            f"Salam! 👋\n\n"
            f"Mən Yonca AI - sizin şəxsi fermer köməkçinizəm.\n\n"
            f"Hazırda **{farm.name}** ({farm.region}) üzərində işləyirik.\n\n"
            "Sizə necə kömək edə bilərəm?"
        )
    
    # Help keywords
    if any(word in msg_lower for word in ["kömək", "help", "nə edə bilərsən", "imkan"]):
        return (
            "🌿 **Yonca AI ilə nə edə bilərsiniz:**\n\n"
            "🌊 **Suvarma** - \"Nə vaxt suvarmalıyam?\"\n"
            "🌱 **Gübrələmə** - \"Gübrə lazımdırmı?\"\n"
            "🐛 **Xəstəliklər** - \"Xəstəlik riski varmı?\"\n"
            "📋 **Cədvəl** - \"Bu gün nə edim?\"\n"
            "🌤️ **Hava** - \"Hava necə olacaq?\"\n"
            "🐄 **Heyvandarlıq** - \"Peyvənd lazımdırmı?\"\n\n"
            "*İstənilən sualınızı Azərbaycan dilində yaza bilərsiniz!*"
        )
    
    # Plan/schedule keywords (fallback)
    if any(word in msg_lower for word in ["bu gün", "plan", "cədvəl", "nə edim", "işlər"]):
        return (
            f"📋 **{datetime.now().strftime('%d.%m.%Y')} üçün plan:**\n\n"
            "1. **06:00** - Sahə müayinəsi\n"
            "2. **07:00** - Suvarma (əgər lazımdırsa)\n"
            "3. **09:00** - Gübrə tətbiqi\n"
            "4. **11:00-16:00** - İstirahət (günorta istisi)\n"
            "5. **17:00** - Avadanlıq baxımı\n\n"
            "📌 *\"Gündəlik Plan\" tabına baxın detallı cədvəl üçün.*"
        )
    
    # Default response with detected intent info
    return (
        "🤔 Sualınızı tam başa düşmədim.\n\n"
        "Aşağıdakı mövzularda kömək edə bilərəm:\n"
        "• Suvarma tövsiyələri\n"
        "• Gübrələmə planı\n"
        "• Xəstəlik/zərərverici monitorinqi\n"
        "• Gündəlik iş cədvəli\n"
        "• Hava proqnozu\n\n"
        "*Yenidən soruşun və ya \"Kömək\" yazın.*"
    )


# ============= INJECT CSS =============

st.markdown(get_all_styles(), unsafe_allow_html=True)


# ============= HEADER =============

st.markdown(
    render_header(
        title="Yonca AI",
        subtitle="Şəxsi Fermer Köməkçiniz",
        icon="🌿"
    ),
    unsafe_allow_html=True
)


# ============= SCENARIO SWITCHER =============

st.markdown("### 🔄 Təsərrüfat Seçimi")

# Create columns for scenario buttons
cols = st.columns(5)

for idx, profile in enumerate(ScenarioProfile):
    label = SCENARIO_LABELS[profile]
    with cols[idx]:
        is_active = st.session_state.current_profile == profile
        
        if st.button(
            f"{label['icon']}\n{label['name'][:8]}...",
            key=f"switcher_scenario_{profile.value}_{idx}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.current_profile = profile
            # Load canonical farm and adapt for UI
            scenario_id = SCENARIO_MAP.get(profile)
            canonical_farm = st.session_state.scenario_farms.get(scenario_id)
            if canonical_farm:
                st.session_state.current_farm = adapt_farm_profile(canonical_farm, profile)
            st.session_state.recommendations = None  # Reset recommendations
            st.rerun()

st.markdown("---")


# ============= GET CURRENT FARM DATA =============

current_farm = st.session_state.current_farm
label = SCENARIO_LABELS[st.session_state.current_profile]


# ============= PROFILE OVERVIEW CARD =============

def build_profile_stats():
    """Build stats list based on farm type."""
    stats = []
    
    if current_farm.soil:
        stats.append(("Torpaq nəmliyi", f"{current_farm.soil.moisture_percent}%"))
        stats.append(("Torpaq pH", f"{current_farm.soil.ph_level}"))
    
    if current_farm.weather:
        stats.append(("Temperatur", f"{current_farm.weather.temperature_current}°C"))
        stats.append(("Rütubət", f"{current_farm.weather.humidity_percent}%"))
    
    if current_farm.crops:
        stats.append(("Bitkilər", f"{len(current_farm.crops)} növ"))
    
    if current_farm.livestock:
        total_animals = sum(l.count for l in current_farm.livestock)
        stats.append(("Heyvanlar", f"{total_animals} baş"))
    
    return stats[:4]  # Max 4 stats for layout


# Build alert message if applicable
alert_msg = ""
if current_farm.satellite_alert:
    alert_msg = current_farm.satellite_alert
elif (current_farm.weather and 
      current_farm.weather.humidity_percent > 70 and 
      current_farm.weather.temperature_max > 32):
    alert_msg = "İstilik stresi riski: Yüksək temperatur + rütubət"

st.markdown(
    render_profile_card(
        name=current_farm.name,
        icon=label["icon"],
        farm_type=label["name"],
        region=current_farm.region,
        area=current_farm.area_hectares,
        stats=build_profile_stats(),
        alert=alert_msg
    ),
    unsafe_allow_html=True
)


# ============= TABS: Recommendations | Timeline | Chat =============

tab_recs, tab_timeline, tab_chat = st.tabs([
    "📋 Tövsiyələr",
    "📅 Gündəlik Plan",
    "💬 Söhbət"
])


# ============= TAB 1: AI RECOMMENDATIONS =============

with tab_recs:
    st.markdown("### 🤖 AI Tövsiyələri")
    st.markdown(
        f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;'>"
        "Qwen2.5-7B modeli tərəfindən hazırlanmış şəxsi tövsiyələr"
        "</p>",
        unsafe_allow_html=True
    )
    
    # Generate recommendations button
    if st.button("🔄 Tövsiyələri Yenilə", type="primary", use_container_width=True):
        with st.spinner("AI təhlil edir..."):
            # Generate recommendations using sidecar service
            st.session_state.recommendations = generate_ui_recommendations(
                current_farm,
                st.session_state.recommendation_service
            )
            st.session_state.request_counter += 1
    
    # Display recommendations
    if st.session_state.recommendations:
        payload = st.session_state.recommendations
        
        # Summary
        st.markdown(
            f"""
            <div style="background:{COLORS['secondary_light']};padding:12px;border-radius:10px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.85rem;color:{COLORS['text_secondary']};">
                        🎯 {payload.total_count} tövsiyə tapıldı
                    </span>
                    <span style="font-size:0.75rem;color:{COLORS['critical']};">
                        🚨 {payload.critical_count} kritik
                    </span>
                </div>
                <div style="font-size:0.7rem;color:{COLORS['text_secondary']};margin-top:4px;">
                    ⚡ {payload.processing_time_ms}ms | 🤖 {payload.inference_engine}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Render each recommendation card
        for rec in payload.recommendations:
            st.markdown(
                render_insight_card(
                    title=rec.title,
                    description=rec.description,
                    action=rec.action,
                    priority=rec.priority,
                    why_title=rec.why_title,
                    why_content=rec.why_explanation,
                    confidence=rec.confidence,
                    time_slot=rec.suggested_time or ""
                ),
                unsafe_allow_html=True
            )
    else:
        st.info("Tövsiyələri görmək üçün yuxarıdakı düyməni basın.")


# ============= TAB 2: DAILY TIMELINE =============

with tab_timeline:
    st.markdown("### 📅 Gündəlik Cədvəl")
    st.markdown(
        f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;'>"
        f"Bu gün: {datetime.now().strftime('%d.%m.%Y')}"
        "</p>",
        unsafe_allow_html=True
    )
    
    # Generate or get timeline
    if st.session_state.recommendations:
        routine = st.session_state.recommendations.daily_routine
        
        # Render timeline
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        
        for item in routine:
            st.markdown(
                render_timeline_item(
                    time=item.time_slot,
                    title=item.title,
                    description=item.description,
                    icon=item.icon,
                    duration=item.duration_minutes,
                    priority=item.priority
                ),
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Gündəlik cədvəl üçün əvvəlcə tövsiyələri yükləyin.")


# ============= TAB 3: CHAT =============

with tab_chat:
    st.markdown("### 💬 Yonca AI ilə Söhbət")
    
    # Quick reply suggestions
    quick_replies = [
        "Nə vaxt suvarmalıyam?",
        "Gübrə lazımdırmı?",
        "Xəstəlik riski varmı?",
        "Bu gün nə edim?",
        "Hava necə olacaq?",
    ]
    
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        if not st.session_state.chat_history:
            # Welcome message
            st.markdown(
                render_chat_bubble(
                    "Salam! 👋 Mən Yonca AI köməkçisiyəm. "
                    f"Hazırda **{current_farm.name}** təsərrüfatı üzərində işləyirik. "
                    "Sizə necə kömək edə bilərəm?",
                    is_user=False,
                    timestamp=datetime.now().strftime("%H:%M")
                ),
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.chat_history:
                st.markdown(
                    render_chat_bubble(
                        msg["content"],
                        is_user=msg["is_user"],
                        timestamp=msg["timestamp"]
                    ),
                    unsafe_allow_html=True
                )
    
    # Quick reply buttons
    st.markdown("**Sürətli suallar:**")
    cols = st.columns(2)
    for idx, reply in enumerate(quick_replies):
        with cols[idx % 2]:
            if st.button(reply, key=f"quick_{idx}", use_container_width=True):
                # Add user message
                st.session_state.chat_history.append({
                    "content": reply,
                    "is_user": True,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Generate bot response
                response = generate_chat_response(reply, current_farm)
                st.session_state.chat_history.append({
                    "content": response,
                    "is_user": False,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                st.rerun()
    
    # Free text input
    user_input = st.chat_input("Sualınızı yazın...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append({
            "content": user_input,
            "is_user": True,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Generate bot response
        response = generate_chat_response(user_input, current_farm)
        st.session_state.chat_history.append({
            "content": response,
            "is_user": False,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        st.rerun()


# ============= FOOTER =============

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center;color:{COLORS['text_secondary']};font-size:0.75rem;">
        🌿 Yonca AI v0.2.0 | Digital Umbrella Prototype<br>
        100% Sintetik Data | Qwen2.5-7B Simulated Inference<br>
        © 2026 Digital Umbrella
    </div>
    """,
    unsafe_allow_html=True
)


# ============= SIDEBAR (Hidden but available) =============

with st.sidebar:
    st.markdown("### ⚙️ Tənzimləmələr")
    
    st.markdown("**Dil / Language:**")
    language = st.selectbox(
        "Seçin",
        ["🇦🇿 Azərbaycan", "🇬🇧 English", "🇷🇺 Русский"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("**Mövzu / Theme:**")
    theme = st.radio(
        "Seçin",
        ["🌿 Yaşıl (Default)", "🌙 Qaranlıq"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("**Sistem Məlumatı:**")
    st.code(f"""
Profil: {st.session_state.current_profile.value}
API Sorğuları: {st.session_state.request_counter}
Chat Mesajları: {len(st.session_state.chat_history)}
    """)
    
    if st.button("🗑️ Söhbəti Təmizlə"):
        st.session_state.chat_history = []
        st.rerun()
