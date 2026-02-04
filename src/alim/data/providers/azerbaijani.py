# src/ALİM/data/providers/azerbaijani.py
"""Custom Faker provider for Azerbaijani agricultural data.

Generates realistic data matching EKTİS (Electronic Agriculture Information System)
formats and Azerbaijani agricultural context.
"""

import hashlib
import math
import random
from datetime import date, timedelta
from typing import Any

from faker.providers import BaseProvider


class AzerbaijaniAgrarianProvider(BaseProvider):
    """Custom Faker provider for Azerbaijani agricultural data.

    Provides generation of:
    - EKTIS-format IDs (parcel, declaration)
    - Azerbaijani names (male/female)
    - Regional data (coordinates, codes)
    - Agricultural data (crops, soil types, irrigation)
    - Weather and NDVI time series
    """

    # ===== Names =====
    MALE_FIRST_NAMES = [
        "Əli",
        "Məmməd",
        "Rəşad",
        "Fərid",
        "Elvin",
        "Rauf",
        "Ülvi",
        "Vüqar",
        "Kamran",
        "Nicat",
        "Əhməd",
        "Turqut",
        "Elşən",
        "Rəşid",
        "Sənan",
        "İlqar",
        "Nurlan",
        "Anar",
        "Elnur",
        "Tural",
        "Emin",
        "Orxan",
        "Cavid",
        "Mətin",
        "Həsən",
        "Hüseyn",
        "Kənan",
        "Fuad",
        "Asif",
    ]

    FEMALE_FIRST_NAMES = [
        "Aygün",
        "Günay",
        "Leyla",
        "Nigar",
        "Səbinə",
        "Gülnar",
        "Fidan",
        "Könül",
        "Nərminə",
        "Aytac",
        "Sevda",
        "Şəbnəm",
        "Lalə",
        "Aytən",
        "Türkan",
        "Günel",
        "Nübar",
        "Afət",
        "Samirə",
        "Rəna",
        "Röya",
        "Pərvanə",
        "Ləman",
        "Xədicə",
        "Fatimə",
        "Aynur",
        "Ülviyyə",
    ]

    LAST_NAMES = [
        "Məmmədov",
        "Əliyev",
        "Həsənov",
        "Hüseynov",
        "Quliyev",
        "Qasımov",
        "Babayev",
        "Bayramov",
        "İsmayılov",
        "Cəfərov",
        "Nəsirov",
        "Rəhimov",
        "Seyidov",
        "Əsgərov",
        "Kazımov",
        "Muradov",
        "Orucov",
        "Əhmədov",
        "Yusifov",
        "Kərimov",
        "Sultanov",
        "Vəliyev",
        "Ağayev",
        "Rüstəmov",
    ]

    # ===== Regions =====
    REGIONS = {
        "Aran": {
            "code": "ARN",
            "center": (40.00, 48.50),
            "primary_crops": ["Buğda", "Pambıq", "Qarğıdalı"],
            "farm_types": ["crop"],
            "climate": "semi-arid",
        },
        "Quba-Qusar": {
            "code": "QUB",
            "center": (41.36, 48.51),
            "primary_crops": ["Alma", "Armud", "Üzüm"],
            "farm_types": ["orchard"],
            "climate": "temperate",
        },
        "Şəki-Zaqatala": {
            "code": "SKI",
            "center": (41.19, 47.17),
            "primary_crops": ["Fındıq", "Tütün"],
            "farm_types": ["orchard", "livestock"],
            "climate": "humid-subtropical",
        },
        "Mil-Muğan": {
            "code": "MUG",
            "center": (39.75, 48.00),
            "primary_crops": ["Pambıq", "Buğda"],
            "farm_types": ["crop"],
            "climate": "semi-arid",
        },
        "Lənkəran": {
            "code": "LNK",
            "center": (38.75, 48.85),
            "primary_crops": ["Pomidor", "Xıyar", "Çay"],
            "farm_types": ["mixed", "orchard"],
            "climate": "humid-subtropical",
        },
        "Abşeron": {
            "code": "ABS",
            "center": (40.37, 49.84),
            "primary_crops": ["Üzüm", "Pomidor", "Xıyar"],
            "farm_types": ["mixed"],
            "climate": "semi-arid",
        },
        "Gəncə-Daşkəsən": {
            "code": "GNC",
            "center": (40.68, 46.36),
            "primary_crops": ["Üzüm", "Buğda", "Kartof"],
            "farm_types": ["crop", "orchard"],
            "climate": "continental",
        },
    }

    # ===== Crops =====
    CROPS_BY_TYPE = {
        "grain": ["Buğda", "Arpa", "Qarğıdalı", "Düyü"],
        "industrial": ["Pambıq", "Tütün", "Günəbaxan"],
        "vegetable": ["Pomidor", "Xıyar", "Bibər", "Soğan", "Kartof", "Kələm"],
        "fruit": ["Üzüm", "Alma", "Armud", "Nar", "Şaftalı", "Heyva"],
        "nut": ["Fındıq", "Qoz"],
        "other": ["Çay"],
    }

    ALL_CROPS = [crop for crops in CROPS_BY_TYPE.values() for crop in crops]

    # ===== Soil Types =====
    SOIL_TYPES = {
        "Münbit": {"quality": "excellent", "drainage": "good"},
        "Gilli": {"quality": "good", "drainage": "poor"},
        "Qumlu": {"quality": "fair", "drainage": "excellent"},
        "Şoranlıq": {"quality": "poor", "drainage": "fair"},
        "Qaratorpaq": {"quality": "excellent", "drainage": "good"},
        "Allüvial": {"quality": "good", "drainage": "good"},
    }

    # ===== Irrigation =====
    IRRIGATION_TYPES = {
        "damcı": {"efficiency": 0.95, "cost": "high"},
        "pivot": {"efficiency": 0.85, "cost": "high"},
        "şırım": {"efficiency": 0.60, "cost": "low"},
        "sel": {"efficiency": 0.45, "cost": "low"},
        "yağmurlama": {"efficiency": 0.75, "cost": "medium"},
        "yağışla": {"efficiency": 0.0, "cost": "none"},
    }

    # ===== Farm Names =====
    FARM_NAME_PREFIXES = [
        "Şərq",
        "Qərb",
        "Cənub",
        "Şimal",
        "Mərkəzi",
        "Yeni",
        "Köhnə",
        "Böyük",
        "Kiçik",
        "Yaşıl",
        "Qızıl",
        "Gümüş",
    ]

    FARM_NAME_SUFFIXES = [
        "Təsərrüfatı",
        "Ferması",
        "Bağı",
        "Sahəsi",
        "Torpağı",
    ]

    # ===== Experience Personas =====
    PERSONAS = {
        "novice": {
            "experience_level": "novice",
            "farming_years_range": (0, 3),
            "education_weights": {
                "primary": 0.3,
                "secondary": 0.5,
                "technical": 0.15,
                "university": 0.05,
            },
            "farm_count_range": (1, 1),
        },
        "experienced": {
            "experience_level": "intermediate",
            "farming_years_range": (4, 15),
            "education_weights": {
                "primary": 0.1,
                "secondary": 0.4,
                "technical": 0.35,
                "university": 0.15,
            },
            "farm_count_range": (1, 2),
        },
        "commercial": {
            "experience_level": "intermediate",
            "farming_years_range": (8, 20),
            "education_weights": {
                "primary": 0.0,
                "secondary": 0.2,
                "technical": 0.3,
                "university": 0.5,
            },
            "farm_count_range": (2, 5),
        },
        "traditional": {
            "experience_level": "expert",
            "farming_years_range": (25, 50),
            "education_weights": {
                "primary": 0.3,
                "secondary": 0.5,
                "technical": 0.15,
                "university": 0.05,
            },
            "farm_count_range": (1, 2),
        },
        "diversified": {
            "experience_level": "intermediate",
            "farming_years_range": (5, 15),
            "education_weights": {
                "primary": 0.1,
                "secondary": 0.3,
                "technical": 0.35,
                "university": 0.25,
            },
            "farm_count_range": (2, 4),
        },
    }

    # ===== ID Generation =====

    def parcel_id(self, region: str | None = None) -> str:
        """Generate EKTIS-format parcel ID.

        Format: AZ-{REGION_CODE}-{4_DIGIT_NUMBER}
        Example: AZ-ARN-1234
        """
        if region is None:
            region = self.random_element(list(self.REGIONS.keys()))

        region_code = self.REGIONS[region]["code"]
        number = self.random_int(1000, 9999)
        return f"AZ-{region_code}-{number}"

    def declaration_id(self, year: int | None = None) -> str:
        """Generate sowing declaration ID.

        Format: DECL-{YEAR}-{6_DIGIT_NUMBER}
        Example: DECL-2026-123456
        """
        if year is None:
            year = date.today().year

        number = self.random_int(100000, 999999)
        return f"DECL-{year}-{number}"

    def user_id(self, index: int | None = None) -> str:
        """Generate synthetic user ID.

        Format: syn_user_{3_DIGIT_NUMBER}
        Example: syn_user_001
        """
        if index is None:
            index = self.random_int(1, 999)
        return f"syn_user_{index:03d}"

    def farm_id(self, user_index: int, farm_index: int = 0) -> str:
        """Generate synthetic farm ID.

        Format: syn_farm_{USER_INDEX}{LETTER}
        Example: syn_farm_001a
        """
        letter = chr(ord("a") + farm_index)
        return f"syn_farm_{user_index:03d}{letter}"

    def reading_id(self, parcel_id: str, reading_date: date) -> str:
        """Generate NDVI reading ID.

        Format: NDVI-{PARCEL_ID_SUFFIX}-{DATE}
        Example: NDVI-ARN-1234-20260115
        """
        parcel_suffix = parcel_id.replace("AZ-", "")
        date_str = reading_date.strftime("%Y%m%d")
        return f"NDVI-{parcel_suffix}-{date_str}"

    def crop_rotation_id(self, parcel_id: str, year: int) -> str:
        """Generate crop rotation log ID.

        Format: ROT-{PARCEL_ID_SUFFIX}-{YEAR}
        Example: ROT-ARN-1234-2025
        """
        parcel_suffix = parcel_id.replace("AZ-", "")
        return f"ROT-{parcel_suffix}-{year}"

    # ===== Name Generation =====

    def azerbaijani_male_name(self) -> str:
        """Generate an Azerbaijani male first name."""
        return self.random_element(self.MALE_FIRST_NAMES)

    def azerbaijani_female_name(self) -> str:
        """Generate an Azerbaijani female first name."""
        return self.random_element(self.FEMALE_FIRST_NAMES)

    def azerbaijani_last_name(self, female: bool = False) -> str:
        """Generate an Azerbaijani last name (with gender suffix)."""
        base_name = self.random_element(self.LAST_NAMES)
        if female:
            # Convert -ov/-yev to -ova/-yeva
            if base_name.endswith("ov"):
                return base_name + "a"
            elif base_name.endswith("yev"):
                return base_name + "a"
        return base_name

    def azerbaijani_full_name(self, female: bool | None = None) -> str:
        """Generate a full Azerbaijani name."""
        if female is None:
            female = self.random_element([True, False])

        if female:
            first = self.azerbaijani_female_name()
        else:
            first = self.azerbaijani_male_name()

        last = self.azerbaijani_last_name(female=female)
        return f"{first} {last}"

    def masked_name(self, index: int) -> str:
        """Generate a masked name for privacy.

        Format: [ŞƏXS_{3_DIGIT_NUMBER}]
        Example: [ŞƏXS_001]
        """
        return f"[ŞƏXS_{index:03d}]"

    def phone_hash(self, phone: str | None = None) -> str:
        """Generate a SHA256 hash of a phone number."""
        if phone is None:
            # Generate Azerbaijani phone format: +994 XX XXX XX XX
            prefix = self.random_element(["50", "51", "55", "70", "77"])
            number = self.random_int(1000000, 9999999)
            phone = f"+994{prefix}{number}"

        return hashlib.sha256(phone.encode()).hexdigest()

    # ===== Regional Data =====

    def region(self) -> str:
        """Get a random Azerbaijani agricultural region."""
        return self.random_element(list(self.REGIONS.keys()))

    def region_code(self, region: str | None = None) -> str:
        """Get ISO region code.

        Format: AZ-{CODE}
        Example: AZ-ARN
        """
        if region is None:
            region = self.region()
        return f"AZ-{self.REGIONS[region]['code']}"

    def coordinates(
        self,
        region: str | None = None,
        offset_km: float = 30.0,
    ) -> tuple[float, float]:
        """Generate coordinates within a region.

        Returns (latitude, longitude) with random offset from center.
        """
        if region is None:
            region = self.region()

        center_lat, center_lon = self.REGIONS[region]["center"]

        # Convert km to approximate degrees (1 degree ≈ 111 km)
        offset_deg = offset_km / 111.0

        lat = center_lat + random.uniform(-offset_deg, offset_deg)
        lon = center_lon + random.uniform(-offset_deg, offset_deg)

        # Clamp to Azerbaijan bounds
        lat = max(38.0, min(42.0, lat))
        lon = max(44.0, min(51.0, lon))

        return (round(lat, 6), round(lon, 6))

    # ===== Agricultural Data =====

    def crop(self, region: str | None = None, crop_type: str | None = None) -> str:
        """Get a random crop, optionally filtered by region or type."""
        if crop_type is not None:
            return self.random_element(self.CROPS_BY_TYPE.get(crop_type, self.ALL_CROPS))

        if region is not None and region in self.REGIONS:
            return self.random_element(self.REGIONS[region]["primary_crops"])

        return self.random_element(self.ALL_CROPS)

    def soil_type(self) -> str:
        """Get a random soil type (Azerbaijani name)."""
        return self.random_element(list(self.SOIL_TYPES.keys()))

    def irrigation_type(self, modern_preference: float = 0.5) -> str:
        """Get a random irrigation type.

        Args:
            modern_preference: 0-1, higher = more likely to get modern systems
        """
        if random.random() < modern_preference:
            return self.random_element(["damcı", "pivot", "yağmurlama"])
        return self.random_element(["şırım", "sel", "yağışla"])

    def farm_type(self, region: str | None = None) -> str:
        """Get a random farm type, optionally influenced by region."""
        if region is not None and region in self.REGIONS:
            return self.random_element(self.REGIONS[region]["farm_types"])
        return self.random_element(["crop", "livestock", "orchard", "mixed"])

    def farm_name(self, region: str | None = None, crop: str | None = None) -> str:
        """Generate a realistic Azerbaijani farm name."""
        prefix = self.random_element(self.FARM_NAME_PREFIXES)
        suffix = self.random_element(self.FARM_NAME_SUFFIXES)
        return f"{prefix} {suffix}"

    def area_hectares(
        self,
        farm_type: str | None = None,
        persona: str = "experienced",
    ) -> float:
        """Generate realistic farm area in hectares.

        Ranges vary by farm type and farmer persona.
        """
        # Base ranges by farm type
        ranges = {
            "crop": (3.0, 50.0),
            "livestock": (1.0, 20.0),
            "orchard": (0.5, 10.0),
            "mixed": (2.0, 25.0),
        }

        # Adjust by persona
        multipliers = {
            "novice": 0.5,
            "experienced": 1.0,
            "commercial": 2.0,
            "traditional": 0.8,
            "diversified": 1.2,
        }

        farm_range = ranges.get(farm_type, (2.0, 20.0))
        multiplier = multipliers.get(persona, 1.0)

        area = random.uniform(farm_range[0], farm_range[1]) * multiplier
        return round(area, 2)

    # ===== NDVI Time Series =====

    def ndvi_series(
        self,
        crop: str,
        start_date: date,
        days: int = 270,
        interval_days: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate synthetic NDVI time series for a crop.

        Simulates realistic vegetation growth patterns with:
        - Growth curve based on crop type
        - Random weather stress events
        - Seasonal senescence

        Returns list of {date, ndvi, health_status} dicts.
        """
        readings = []

        # Determine growth pattern based on crop
        # Peak NDVI varies by crop type
        if crop in ["Buğda", "Arpa"]:  # Winter grains
            peak_day = 180  # Late spring peak
            peak_ndvi = 0.85
        elif crop in ["Pambıq", "Qarğıdalı"]:  # Summer crops
            peak_day = 120
            peak_ndvi = 0.80
        elif crop in ["Pomidor", "Xıyar"]:  # Vegetables
            peak_day = 90
            peak_ndvi = 0.75
        elif crop in ["Üzüm", "Alma"]:  # Perennials
            peak_day = 150
            peak_ndvi = 0.82
        else:
            peak_day = 120
            peak_ndvi = 0.78

        # Generate readings at regular intervals
        current_date = start_date
        for day in range(0, days, interval_days):
            # Calculate base NDVI using Gaussian-like growth curve
            progress = (
                day / peak_day if day <= peak_day else 1 + (day - peak_day) / (days - peak_day)
            )

            if progress <= 1:
                # Growth phase: sigmoid curve
                base_ndvi = peak_ndvi * (1 - math.exp(-3 * progress))
            else:
                # Senescence phase: exponential decay
                decay = (progress - 1) * 2
                base_ndvi = peak_ndvi * math.exp(-decay)

            # Add random variation (weather effects)
            noise = random.uniform(-0.05, 0.05)

            # Occasional stress events (drought, disease)
            if random.random() < 0.1:
                noise -= random.uniform(0.1, 0.2)

            ndvi = max(0.05, min(0.95, base_ndvi + noise))
            ndvi = round(ndvi, 3)

            # Determine health status
            if ndvi < 0.2:
                status = "kritik"
            elif ndvi < 0.4:
                status = "stress"
            elif ndvi < 0.6:
                status = "orta"
            elif ndvi < 0.8:
                status = "sağlam"
            else:
                status = "əla"

            readings.append(
                {
                    "date": current_date + timedelta(days=day),
                    "ndvi": ndvi,
                    "health_status": status,
                }
            )

        return readings

    # ===== Weather Data =====

    def weather_event(
        self,
        region: str,
        month: int,
    ) -> dict[str, Any]:
        """Generate a weather event for stress testing.

        Returns dict with event type and severity.
        """
        # Climate-based event probabilities
        climate = self.REGIONS.get(region, {}).get("climate", "continental")

        if climate == "semi-arid" and month in [6, 7, 8]:
            event_weights = {"drought": 0.4, "heatwave": 0.3, "normal": 0.3}
        elif climate == "humid-subtropical" and month in [3, 4, 5]:
            event_weights = {"heavy_rain": 0.3, "flooding": 0.1, "normal": 0.6}
        elif month in [12, 1, 2]:
            event_weights = {"frost": 0.3, "snow": 0.2, "normal": 0.5}
        else:
            event_weights = {"normal": 0.9, "drought": 0.05, "heatwave": 0.05}

        event_type = self.random_element(
            list(event_weights.keys()),
            p=list(event_weights.values()),
        )

        if event_type == "normal":
            return {"event": None, "severity": 0}

        severity = self.random_element([1, 2, 3])  # 1=mild, 2=moderate, 3=severe

        return {
            "event": event_type,
            "severity": severity,
            "description_az": self._weather_description(event_type, severity),
        }

    def _weather_description(self, event: str, severity: int) -> str:
        """Get Azerbaijani description for weather event."""
        descriptions = {
            "drought": {
                1: "Yüngül quraqlıq",
                2: "Orta quraqlıq",
                3: "Şiddətli quraqlıq",
            },
            "heatwave": {
                1: "Yüngül istilik dalğası",
                2: "Orta istilik dalğası",
                3: "Şiddətli istilik dalğası",
            },
            "frost": {
                1: "Yüngül şaxta",
                2: "Orta şaxta",
                3: "Şiddətli şaxta",
            },
            "heavy_rain": {
                1: "Güclü yağış",
                2: "Çox güclü yağış",
                3: "Fövqəladə güclü yağış",
            },
            "flooding": {
                1: "Yüngül daşqın",
                2: "Orta daşqın",
                3: "Şiddətli daşqın",
            },
            "snow": {
                1: "Yüngül qar",
                2: "Güclü qar",
                3: "Qar fırtınası",
            },
        }
        return descriptions.get(event, {}).get(severity, "Naməlum hadisə")

    # ===== Persona Generation =====

    def persona(self, persona_type: str | None = None) -> dict[str, Any]:
        """Generate a complete user persona.

        Returns dict with all user profile attributes.
        """
        if persona_type is None:
            persona_type = self.random_element(list(self.PERSONAS.keys()))

        config = self.PERSONAS[persona_type]

        # Generate weighted education level
        education = self.random_element(
            list(config["education_weights"].keys()),
            p=list(config["education_weights"].values()),
        )

        return {
            "persona_type": persona_type,
            "experience_level": config["experience_level"],
            "farming_years": self.random_int(*config["farming_years_range"]),
            "education_level": education,
            "farm_count": self.random_int(*config["farm_count_range"]),
            "receives_subsidies": self.random_element([True, False]),
            "notification_pref": self.random_element(["sms", "app", "both"]),
            "language_pref": "az_AZ",
            "preferred_units": self.random_element(["metric", "local"]),
        }

    def yield_tons_per_ha(self, crop: str) -> float:
        """Generate realistic yield in tons per hectare.

        Based on Azerbaijani agricultural statistics.
        """
        # Average yields by crop (tons/ha)
        yields = {
            "Buğda": (2.0, 4.5),
            "Arpa": (1.8, 4.0),
            "Qarğıdalı": (4.0, 8.0),
            "Düyü": (3.0, 6.0),
            "Pambıq": (1.5, 3.5),
            "Tütün": (1.0, 2.5),
            "Pomidor": (25.0, 50.0),
            "Xıyar": (20.0, 40.0),
            "Kartof": (15.0, 30.0),
            "Üzüm": (6.0, 12.0),
            "Alma": (8.0, 20.0),
            "Fındıq": (0.8, 2.0),
        }

        crop_range = yields.get(crop, (2.0, 5.0))
        return round(random.uniform(*crop_range), 2)
