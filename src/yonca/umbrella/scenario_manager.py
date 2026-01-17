"""
Yonca AI - Digital Umbrella Scenario Manager
=============================================

Manages synthetic farm profiles for demonstration.
Supports 5 scenarios: Wheat, Livestock, Orchard, Mixed, Poultry.

100% synthetic data - no real farmer data is used.

NOTE: Model Naming
==================
This module defines its own `FarmProfile` dataclass for the Streamlit UI.
The canonical Pydantic models are in `yonca.models`.
The canonical scenario data is in `yonca.data.scenarios`.

The umbrella-specific FarmProfile includes UI-specific fields like
`satellite_alert` that aren't needed in the core data layer.

For future consolidation, consider:
- Using yonca.models.FarmProfile as the base
- Adding UI-specific fields via composition or inheritance
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Any
import random


class ScenarioProfile(str, Enum):
    """Available farm scenario profiles."""
    WHEAT = "wheat"
    LIVESTOCK = "livestock"
    ORCHARD = "orchard"
    MIXED = "mixed"
    POULTRY = "poultry"


# ============= Azerbaijani Labels =============

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


@dataclass
class SoilCondition:
    """Soil condition data for a farm."""
    soil_type: str  # clay, sandy, loamy
    moisture_percent: int  # 0-100
    ph_level: float  # 0-14
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float


@dataclass
class WeatherCondition:
    """Weather condition data."""
    temperature_current: float
    temperature_min: float
    temperature_max: float
    humidity_percent: int  # 0-100
    wind_speed_kmh: float
    condition: str  # sunny, cloudy, rainy, stormy
    precipitation_mm: float
    uv_index: int


@dataclass
class CropData:
    """Crop information."""
    crop_type: str
    variety: str
    growth_stage: str  # germination, vegetative, flowering, fruiting, maturity
    planted_date: date
    harvest_date: Optional[date]
    area_hectares: float
    health_status: str  # healthy, stressed, diseased


@dataclass
class LivestockData:
    """Livestock information."""
    animal_type: str
    count: int
    avg_age_months: int
    health_status: str
    last_vaccination: Optional[date]
    feed_type: str
    housing_condition: str  # good, needs_attention, poor


@dataclass
class FarmProfile:
    """Complete farm profile for a scenario."""
    id: str
    profile_type: ScenarioProfile
    name: str
    region: str
    area_hectares: float
    latitude: float
    longitude: float
    
    # Conditions
    soil: Optional[SoilCondition] = None
    weather: Optional[WeatherCondition] = None
    
    # Assets
    crops: list[CropData] = field(default_factory=list)
    livestock: list[LivestockData] = field(default_factory=list)
    
    # Metadata
    irrigation_system: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Satellite imagery simulation (for wheat scenario)
    satellite_alert: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "profile_type": self.profile_type.value,
            "name": self.name,
            "region": self.region,
            "area_hectares": self.area_hectares,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "soil": {
                "soil_type": self.soil.soil_type,
                "moisture_percent": self.soil.moisture_percent,
                "ph_level": self.soil.ph_level,
                "nitrogen_kg_ha": self.soil.nitrogen_kg_ha,
                "phosphorus_kg_ha": self.soil.phosphorus_kg_ha,
                "potassium_kg_ha": self.soil.potassium_kg_ha,
            } if self.soil else None,
            "weather": {
                "temperature_current": self.weather.temperature_current,
                "temperature_min": self.weather.temperature_min,
                "temperature_max": self.weather.temperature_max,
                "humidity_percent": self.weather.humidity_percent,
                "wind_speed_kmh": self.weather.wind_speed_kmh,
                "condition": self.weather.condition,
                "precipitation_mm": self.weather.precipitation_mm,
                "uv_index": self.weather.uv_index,
            } if self.weather else None,
            "crops": [
                {
                    "crop_type": c.crop_type,
                    "variety": c.variety,
                    "growth_stage": c.growth_stage,
                    "area_hectares": c.area_hectares,
                    "health_status": c.health_status,
                } for c in self.crops
            ],
            "livestock": [
                {
                    "animal_type": l.animal_type,
                    "count": l.count,
                    "health_status": l.health_status,
                    "housing_condition": l.housing_condition,
                } for l in self.livestock
            ],
            "irrigation_system": self.irrigation_system,
            "satellite_alert": self.satellite_alert,
        }


class ScenarioManager:
    """
    Manages synthetic farm scenarios for demonstration.
    
    Toggle between 5 profiles:
    - Wheat: Grain farming with irrigation challenges
    - Livestock: Cattle/sheep farm with health monitoring
    - Orchard: Fruit trees with pest management
    - Mixed: Diversified small farm
    - Poultry: Chicken farm with climate control
    """
    
    def __init__(self):
        self._scenarios: dict[ScenarioProfile, FarmProfile] = {}
        self._current_profile: ScenarioProfile = ScenarioProfile.WHEAT
        self._initialize_scenarios()
    
    def _initialize_scenarios(self) -> None:
        """Initialize all synthetic farm scenarios."""
        
        # ============= SCENARIO 1: WHEAT FARM =============
        # Specific logic: Soil moisture 12%, satellite shows yellowing
        self._scenarios[ScenarioProfile.WHEAT] = FarmProfile(
            id="scenario-wheat-umbrella",
            profile_type=ScenarioProfile.WHEAT,
            name="Aran Taxıl Təsərrüfatı",
            region="Aran",
            area_hectares=85.0,
            latitude=40.1234,
            longitude=47.5678,
            soil=SoilCondition(
                soil_type="clay",
                moisture_percent=12,  # Critical low - needs irrigation
                ph_level=6.8,
                nitrogen_kg_ha=22.0,  # Low nitrogen - visible yellowing
                phosphorus_kg_ha=18.0,
                potassium_kg_ha=85.0,
            ),
            weather=WeatherCondition(
                temperature_current=28.0,
                temperature_min=18.0,
                temperature_max=32.0,
                humidity_percent=35,
                wind_speed_kmh=12.0,
                condition="sunny",
                precipitation_mm=0.0,
                uv_index=7,
            ),
            crops=[
                CropData(
                    crop_type="buğda",
                    variety="Qobustan",
                    growth_stage="flowering",
                    planted_date=date.today() - timedelta(days=90),
                    harvest_date=date.today() + timedelta(days=30),
                    area_hectares=60.0,
                    health_status="stressed",  # Due to low moisture
                ),
                CropData(
                    crop_type="arpa",
                    variety="Şirvan",
                    growth_stage="flowering",
                    planted_date=date.today() - timedelta(days=85),
                    harvest_date=date.today() + timedelta(days=25),
                    area_hectares=20.0,
                    health_status="healthy",
                ),
            ],
            irrigation_system="arxlı",
            satellite_alert="Cənub-şərq sahəsində lokal sarılma aşkarlandı (NDVI anomaliya)",
        )
        
        # ============= SCENARIO 2: LIVESTOCK FARM =============
        # Specific logic: High humidity + rising temps = ventilation risk
        self._scenarios[ScenarioProfile.LIVESTOCK] = FarmProfile(
            id="scenario-livestock-umbrella",
            profile_type=ScenarioProfile.LIVESTOCK,
            name="Qazax Heyvandarlıq Ferması",
            region="Gəncə-Qazax",
            area_hectares=45.0,
            latitude=40.6789,
            longitude=46.3456,
            weather=WeatherCondition(
                temperature_current=31.0,
                temperature_min=22.0,
                temperature_max=36.0,  # High - heat stress risk
                humidity_percent=78,    # High humidity in barn
                wind_speed_kmh=5.0,     # Low wind - poor ventilation
                condition="cloudy",
                precipitation_mm=0.0,
                uv_index=5,
            ),
            livestock=[
                LivestockData(
                    animal_type="mal-qara",
                    count=35,
                    avg_age_months=24,
                    health_status="sağlam",
                    last_vaccination=date.today() - timedelta(days=200),
                    feed_type="yonca + qarğıdalı",
                    housing_condition="needs_attention",  # Ventilation issue
                ),
                LivestockData(
                    animal_type="qoyun",
                    count=120,
                    avg_age_months=18,
                    health_status="yaxşı",
                    last_vaccination=date.today() - timedelta(days=90),
                    feed_type="otlaq + yem",
                    housing_condition="good",
                ),
            ],
        )
        
        # ============= SCENARIO 3: ORCHARD FARM =============
        self._scenarios[ScenarioProfile.ORCHARD] = FarmProfile(
            id="scenario-orchard-umbrella",
            profile_type=ScenarioProfile.ORCHARD,
            name="Quba Alma Bağları",
            region="Quba-Xaçmaz",
            area_hectares=25.0,
            latitude=41.3612,
            longitude=48.5234,
            soil=SoilCondition(
                soil_type="loamy",
                moisture_percent=35,
                ph_level=6.2,
                nitrogen_kg_ha=40.0,
                phosphorus_kg_ha=22.0,  # Low for fruiting
                potassium_kg_ha=75.0,   # Low for fruit quality
            ),
            weather=WeatherCondition(
                temperature_current=24.0,
                temperature_min=15.0,
                temperature_max=28.0,
                humidity_percent=65,
                wind_speed_kmh=8.0,
                condition="cloudy",
                precipitation_mm=2.0,
                uv_index=4,
            ),
            crops=[
                CropData(
                    crop_type="alma",
                    variety="Quba",
                    growth_stage="fruiting",
                    planted_date=date.today() - timedelta(days=1825),
                    harvest_date=date.today() + timedelta(days=45),
                    area_hectares=15.0,
                    health_status="healthy",
                ),
                CropData(
                    crop_type="armud",
                    variety="Villyams",
                    growth_stage="fruiting",
                    planted_date=date.today() - timedelta(days=1460),
                    harvest_date=date.today() + timedelta(days=60),
                    area_hectares=8.0,
                    health_status="healthy",
                ),
            ],
            irrigation_system="damcı suvarma",
        )
        
        # ============= SCENARIO 4: MIXED FARM =============
        self._scenarios[ScenarioProfile.MIXED] = FarmProfile(
            id="scenario-mixed-umbrella",
            profile_type=ScenarioProfile.MIXED,
            name="Şəki Qarışıq Təsərrüfatı",
            region="Şəki-Zaqatala",
            area_hectares=12.0,
            latitude=41.1912,
            longitude=47.1706,
            soil=SoilCondition(
                soil_type="loamy",
                moisture_percent=42,
                ph_level=6.5,
                nitrogen_kg_ha=45.0,
                phosphorus_kg_ha=28.0,
                potassium_kg_ha=95.0,
            ),
            weather=WeatherCondition(
                temperature_current=22.0,
                temperature_min=14.0,
                temperature_max=26.0,
                humidity_percent=55,
                wind_speed_kmh=10.0,
                condition="sunny",
                precipitation_mm=0.0,
                uv_index=6,
            ),
            crops=[
                CropData(
                    crop_type="pomidor",
                    variety="yerli",
                    growth_stage="fruiting",
                    planted_date=date.today() - timedelta(days=60),
                    harvest_date=date.today() + timedelta(days=15),
                    area_hectares=3.0,
                    health_status="healthy",
                ),
                CropData(
                    crop_type="xiyar",
                    variety="Bakı",
                    growth_stage="fruiting",
                    planted_date=date.today() - timedelta(days=45),
                    harvest_date=date.today() + timedelta(days=20),
                    area_hectares=2.0,
                    health_status="healthy",
                ),
            ],
            livestock=[
                LivestockData(
                    animal_type="inək",
                    count=5,
                    avg_age_months=36,
                    health_status="sağlam",
                    last_vaccination=date.today() - timedelta(days=60),
                    feed_type="otlaq",
                    housing_condition="good",
                ),
            ],
            irrigation_system="şlanqlı",
        )
        
        # ============= SCENARIO 5: POULTRY FARM =============
        self._scenarios[ScenarioProfile.POULTRY] = FarmProfile(
            id="scenario-poultry-umbrella",
            profile_type=ScenarioProfile.POULTRY,
            name="Lənkəran Quşçuluq Ferması",
            region="Lənkəran",
            area_hectares=3.0,
            latitude=38.7534,
            longitude=48.8510,
            weather=WeatherCondition(
                temperature_current=29.0,
                temperature_min=21.0,
                temperature_max=33.0,
                humidity_percent=72,  # High humidity - subtropical
                wind_speed_kmh=6.0,
                condition="cloudy",
                precipitation_mm=5.0,
                uv_index=5,
            ),
            livestock=[
                LivestockData(
                    animal_type="toyuq",
                    count=2500,
                    avg_age_months=8,
                    health_status="yaxşı",
                    last_vaccination=date.today() - timedelta(days=45),
                    feed_type="kombinə yem",
                    housing_condition="good",
                ),
                LivestockData(
                    animal_type="yumurta toyuğu",
                    count=1500,
                    avg_age_months=14,
                    health_status="sağlam",
                    last_vaccination=date.today() - timedelta(days=30),
                    feed_type="yumurta yemi",
                    housing_condition="good",
                ),
            ],
        )
    
    @property
    def current_profile(self) -> ScenarioProfile:
        """Get the current active profile."""
        return self._current_profile
    
    @property
    def current_farm(self) -> FarmProfile:
        """Get the current farm profile."""
        return self._scenarios[self._current_profile]
    
    def switch_profile(self, profile: ScenarioProfile) -> FarmProfile:
        """Switch to a different scenario profile."""
        if profile not in self._scenarios:
            raise ValueError(f"Unknown profile: {profile}")
        self._current_profile = profile
        return self._scenarios[profile]
    
    def get_farm(self, profile: ScenarioProfile) -> FarmProfile:
        """Get a specific farm profile."""
        return self._scenarios.get(profile)
    
    def list_profiles(self) -> list[dict]:
        """List all available profiles with metadata."""
        return [
            {
                "profile": profile,
                "label": SCENARIO_LABELS[profile],
                "farm": self._scenarios[profile],
            }
            for profile in ScenarioProfile
        ]
    
    def get_profile_label(self, profile: ScenarioProfile) -> dict:
        """Get Azerbaijani labels for a profile."""
        return SCENARIO_LABELS.get(profile, {})
    
    def randomize_weather(self, profile: Optional[ScenarioProfile] = None) -> WeatherCondition:
        """Generate random weather variation for demo purposes."""
        farm = self._scenarios.get(profile or self._current_profile)
        if not farm or not farm.weather:
            return None
        
        base = farm.weather
        return WeatherCondition(
            temperature_current=base.temperature_current + random.uniform(-2, 2),
            temperature_min=base.temperature_min + random.uniform(-1, 1),
            temperature_max=base.temperature_max + random.uniform(-1, 3),
            humidity_percent=max(0, min(100, base.humidity_percent + random.randint(-5, 5))),
            wind_speed_kmh=max(0, base.wind_speed_kmh + random.uniform(-3, 3)),
            condition=base.condition,
            precipitation_mm=max(0, base.precipitation_mm + random.uniform(-1, 2)),
            uv_index=max(0, min(11, base.uv_index + random.randint(-1, 1))),
        )


# Singleton instance for easy access
scenario_manager = ScenarioManager()
