# demo-ui/services/mock_data.py
"""Mock data service for demo purposes.

Provides synthetic farm data and weather information for the demo UI
without requiring database access.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class DemoFarm:
    """A demo farm profile."""
    
    id: str
    name: str
    owner: str
    region: str
    district: str
    crop: str
    area_ha: float
    soil_type: str
    irrigation_type: str
    experience_years: int
    last_ndvi: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for LangGraph state."""
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "region": self.region,
            "district": self.district,
            "crop": self.crop,
            "area_ha": self.area_ha,
            "soil_type": self.soil_type,
            "irrigation_type": self.irrigation_type,
            "experience_years": self.experience_years,
            "last_ndvi": self.last_ndvi,
        }


# Demo farm profiles representing different personas
DEMO_FARMS: list[DemoFarm] = [
    DemoFarm(
        id="demo_farm_001",
        name="Günəşli Bağ",
        owner="Əli Məmmədov",
        region="Aran",
        district="Sabirabad",
        crop="pomidor",
        area_ha=2.5,
        soil_type="gilli",
        irrigation_type="damcı",
        experience_years=15,
        last_ndvi=0.72,
    ),
    DemoFarm(
        id="demo_farm_002",
        name="Yaşıl Vadi",
        owner="Leyla Həsənova",
        region="Quba-Xaçmaz",
        district="Quba",
        crop="alma",
        area_ha=5.0,
        soil_type="qumlu-gilli",
        irrigation_type="səpələmə",
        experience_years=8,
        last_ndvi=0.68,
    ),
    DemoFarm(
        id="demo_farm_003",
        name="Bərəkət Ferması",
        owner="Rauf Əliyev",
        region="Şəki-Zaqatala",
        district="Şəki",
        crop="fındıq",
        area_ha=10.0,
        soil_type="münbit",
        irrigation_type="yağış",
        experience_years=20,
        last_ndvi=0.75,
    ),
    DemoFarm(
        id="demo_farm_004",
        name="Novator Təsərrüfatı",
        owner="Nigar Quliyeva",
        region="Lənkəran-Astara",
        district="Lənkəran",
        crop="çay",
        area_ha=3.0,
        soil_type="turşumsu",
        irrigation_type="damcı",
        experience_years=5,
        last_ndvi=0.80,
    ),
    DemoFarm(
        id="demo_farm_005",
        name="Köhnə Kəndin Sahəsi",
        owner="Tural Babayev",
        region="Mil-Muğan",
        district="İmişli",
        crop="pambıq",
        area_ha=15.0,
        soil_type="şoran",
        irrigation_type="arxlarla",
        experience_years=3,
        last_ndvi=0.55,
    ),
]


def get_demo_farms() -> list[dict[str, Any]]:
    """Get all demo farms as dictionaries.
    
    Returns:
        List of farm dictionaries suitable for LangGraph state.
    """
    return [farm.to_dict() for farm in DEMO_FARMS]


def get_demo_farm_by_id(farm_id: str) -> dict[str, Any] | None:
    """Get a specific demo farm by ID.
    
    Args:
        farm_id: The farm ID to look up.
        
    Returns:
        Farm dictionary or None if not found.
    """
    for farm in DEMO_FARMS:
        if farm.id == farm_id:
            return farm.to_dict()
    return None


def get_mock_weather(region: str) -> dict[str, Any]:
    """Get mock weather data for a region.
    
    Args:
        region: The region name (e.g., "Aran", "Quba-Xaçmaz").
        
    Returns:
        Weather data dictionary.
    """
    # Mock weather data by region (summer conditions)
    weather_by_region: dict[str, dict[str, Any]] = {
        "Aran": {
            "temperature_c": 35,
            "humidity_percent": 45,
            "precipitation_mm": 0,
            "wind_speed_ms": 3.5,
            "condition": "günaşlı",
            "forecast": "Növbəti 5 gün quraq, yüksək temperatur gözlənilir.",
        },
        "Quba-Xaçmaz": {
            "temperature_c": 28,
            "humidity_percent": 65,
            "precipitation_mm": 5,
            "wind_speed_ms": 2.0,
            "condition": "buludlu",
            "forecast": "Sabah yağış ehtimalı var.",
        },
        "Şəki-Zaqatala": {
            "temperature_c": 26,
            "humidity_percent": 70,
            "precipitation_mm": 10,
            "wind_speed_ms": 1.5,
            "condition": "yağışlı",
            "forecast": "Həftə ərzində davamlı yağış gözlənilir.",
        },
        "Lənkəran-Astara": {
            "temperature_c": 30,
            "humidity_percent": 80,
            "precipitation_mm": 15,
            "wind_speed_ms": 2.5,
            "condition": "rütubətli",
            "forecast": "Yüksək rütubət davam edəcək.",
        },
        "Mil-Muğan": {
            "temperature_c": 38,
            "humidity_percent": 35,
            "precipitation_mm": 0,
            "wind_speed_ms": 4.0,
            "condition": "isti",
            "forecast": "Həddindən artıq isti günlər gözlənilir.",
        },
    }
    
    # Default weather if region not found
    default_weather = {
        "temperature_c": 30,
        "humidity_percent": 50,
        "precipitation_mm": 0,
        "wind_speed_ms": 2.5,
        "condition": "aydın",
        "forecast": "Normal yay şəraiti gözlənilir.",
    }
    
    weather = weather_by_region.get(region, default_weather)
    weather["region"] = region
    weather["timestamp"] = datetime.now().isoformat()
    
    return weather


class MockDataService:
    """Service for managing mock demo data."""
    
    def __init__(self):
        """Initialize the mock data service."""
        self.farms = DEMO_FARMS
    
    def get_all_farms(self) -> list[dict[str, Any]]:
        """Get all demo farms."""
        return get_demo_farms()
    
    def get_farm(self, farm_id: str) -> dict[str, Any] | None:
        """Get a farm by ID."""
        return get_demo_farm_by_id(farm_id)
    
    def get_weather(self, region: str) -> dict[str, Any]:
        """Get weather for a region."""
        return get_mock_weather(region)
    
    def get_farm_selector_options(self) -> list[dict[str, str]]:
        """Get farm options for the selector widget.
        
        Returns:
            List of {value, label} dicts for Chainlit Select widget.
        """
        options = []
        for farm in self.farms:
            label = f"{farm.name} ({farm.crop}, {farm.region})"
            options.append({
                "value": farm.id,
                "label": label,
            })
        return options
