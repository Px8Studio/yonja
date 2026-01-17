"""
Yonca AI - Umbrella Core Data Definitions
=========================================

This module contains the core data structures and constants used by the
Umbrella UI that need to be importable without triggering Streamlit execution.

These are separated from app.py to avoid circular import issues when
the umbrella package __init__.py re-exports them.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

from yonca.models import FarmProfile


# ============= SCENARIO PROFILES =============

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
        "icon": "🌾",
        "description": "Buğda və arpa yetişdirən fermer",
        "farmer_name": "Əli",
    },
    ScenarioProfile.LIVESTOCK: {
        "name": "Heyvandarlıq",
        "icon": "🐄",
        "description": "Mal-qara və qoyunçuluq",
        "farmer_name": "Məmməd",
    },
    ScenarioProfile.ORCHARD: {
        "name": "Meyvə Bağı",
        "icon": "🍎",
        "description": "Alma və armud bağları",
        "farmer_name": "Fərid",
    },
    ScenarioProfile.MIXED: {
        "name": "Qarışıq",
        "icon": "🌻",
        "description": "Bitki + heyvandarlıq",
        "farmer_name": "Rəşad",
    },
    ScenarioProfile.POULTRY: {
        "name": "Quşçuluq",
        "icon": "🐔",
        "description": "Toyuq və yumurta istehsalı",
        "farmer_name": "Vüqar",
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
    ph_level: float
    moisture_percent: int
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float


@dataclass
class UICropInfo:
    """Crop information adapted for UI display."""
    crop_type: str
    variety: str
    growth_stage: str
    area_hectares: float
    days_to_harvest: int


@dataclass
class UILivestockInfo:
    """Livestock information adapted for UI display."""
    animal_type: str
    count: int
    health_status: str
    vaccination_status: str


@dataclass
class UIFarmProfile:
    """Farm profile adapted for UI display."""
    name: str
    region: str
    area_hectares: float
    profile_type: ScenarioProfile
    weather: Optional[UIWeatherData] = None
    soil: Optional[UISoilData] = None
    crops: Optional[List[UICropInfo]] = None
    livestock: Optional[List[UILivestockInfo]] = None
    satellite_alert: Optional[str] = None


def adapt_farm_profile(farm: FarmProfile, profile_type: ScenarioProfile) -> UIFarmProfile:
    """
    Adapt a canonical FarmProfile to a UI-friendly UIFarmProfile.
    
    This bridges the canonical data model with the UI display requirements,
    generating synthetic weather data and formatting for display.
    """
    # Adapt soil data
    soil = None
    if farm.soil_data:
        soil = UISoilData(
            soil_type=farm.soil_data.soil_type.value if farm.soil_data.soil_type else "unknown",
            ph_level=farm.soil_data.ph_level,
            moisture_percent=int(farm.soil_data.moisture_percent),
            nitrogen_kg_ha=farm.soil_data.nitrogen_level,
            phosphorus_kg_ha=farm.soil_data.phosphorus_level,
            potassium_kg_ha=farm.soil_data.potassium_level,
        )
    
    # Adapt crop data
    crops = None
    if farm.crops:
        crops = [
            UICropInfo(
                crop_type=crop.crop_type,
                variety=crop.variety,
                growth_stage=crop.current_stage.value if crop.current_stage else "unknown",
                area_hectares=crop.area_hectares,
                days_to_harvest=(crop.expected_harvest_date - crop.planting_date).days 
                    if crop.expected_harvest_date and crop.planting_date else 30,
            )
            for crop in farm.crops
        ]
    
    # Adapt livestock data
    livestock = None
    if farm.livestock:
        from datetime import date
        livestock = [
            UILivestockInfo(
                animal_type=animal.livestock_type.value if animal.livestock_type else "unknown",
                count=animal.count,
                health_status=animal.health_status or "unknown",
                vaccination_status="overdue" if (
                    animal.last_vaccination_date and 
                    (date.today() - animal.last_vaccination_date).days > 180
                ) else "current",
            )
            for animal in farm.livestock
        ]
    
    # Generate synthetic weather based on profile type and region
    # (In production, this would come from actual weather API)
    weather = UIWeatherData(
        temperature_current=28.0,
        temperature_min=18.0,
        temperature_max=35.0,
        humidity_percent=65,
        wind_speed_kmh=12.0,
        condition="sunny",
        precipitation_mm=0.0,
        uv_index=7,
    )
    
    # Customize weather based on region
    if farm.location and farm.location.region:
        region = farm.location.region.lower()
        if "quba" in region or "xaçmaz" in region:
            weather.temperature_current = 24.0
            weather.temperature_max = 30.0
            weather.humidity_percent = 75
        elif "lənkəran" in region:
            weather.humidity_percent = 80
            weather.condition = "partly_cloudy"
    
    # Generate satellite alert for wheat farm with low nitrogen
    satellite_alert = None
    if profile_type == ScenarioProfile.WHEAT and soil and soil.nitrogen_kg_ha < 30:
        satellite_alert = "Peyk: Şimal sahəsində kloroz əlamətləri aşkarlandı"
    
    return UIFarmProfile(
        name=farm.name,
        region=farm.location.region if farm.location else "Bilinmir",
        area_hectares=farm.total_area_hectares,
        profile_type=profile_type,
        weather=weather,
        soil=soil,
        crops=crops,
        livestock=livestock,
        satellite_alert=satellite_alert,
    )
