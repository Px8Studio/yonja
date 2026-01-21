# demo-ui/alem_persona.py
"""ALEM Persona Provisioning System — JIT (Just-In-Time) Agricultural Identity.

This module implements "Persona Wrapping" — a mechanism to enrich Google OAuth
identities with synthetic agricultural context. When a farmer logs in with
minimal Google claims, we auto-generate a complete ALEM persona (FIN, region,
crops, farm size) to ensure the demo always shows rich, personalized advice.

Architecture:
    Google OAuth (minimal data)
         ↓
    provision_alem_persona()
         ↓
    Check if ALEM_Persona exists
         ↓
    If not: Generate synthetic farmer profile
         ↓
    ALEM Persona (rich context)
         ↓
    Chainlit session + Langfuse metadata
         ↓
    LangGraph agent uses persona for context-aware recommendations

This approach proves that ALEM will seamlessly integrate with mygov ID
by simply replacing the OAuth source — the persona wrapping logic remains
the same, just reading from government claims instead of generating synthetic ones.
"""

import random
import secrets
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ============================================
# ALEM Persona Constants
# ============================================

# Azerbaijani agricultural regions
AZERBAIJANI_REGIONS = [
    "Sabirabad",  # Major cotton, vegetables
    "Quba",  # Apple orchards, mountainous
    "Gəncə",  # Wheat, barley
    "Şəki",  # Cherry, hazelnut
    "Lənkəran",  # Tea, citrus
    "Muğan",  # Cotton, grain
    "Karabakh",  # Recently liberated, grain focus
    "Siyəzən",  # Livestock, grain
    "Masallı",  # Vegetables, tea
    "Aran",  # Mixed farming, cotton
]

# Primary crops in Azerbaijan
AZERBAIJANI_CROPS = {
    "Pambıq": "Cotton",  # Primary export
    "Buğda": "Wheat",  # Staple grain
    "Alma": "Apple",  # High-value orchards
    "Üzüm": "Grape",  # Vineyards
    "Pomidor": "Tomato",  # High-value vegetables
    "Fındıq": "Hazelnut",  # Premium crop
    "Çay": "Tea",  # Specialty (Lənkəran)
    "Sitrus": "Citrus",  # Modern expansion
    "Qarğıdalı": "Corn",  # Animal feed, ethanol
    "Soya": "Soybean",  # Emerging crop
}

# Farm sizes (hectares) — typical Azerbaijani farm distribution
FARM_SIZE_RANGES = {
    "small": (2.0, 10.0),  # Small family farm
    "medium": (10.0, 30.0),  # Cooperative/commercial
    "large": (30.0, 100.0),  # Commercial enterprise
}

# Farmer experience levels
FARMER_EXPERIENCE = ["novice", "intermediate", "expert"]


# Mock FIN code format: 1-9 (first digit) + XYZ + 000-999
# Simulates Azerbaijani FIN (Fərdi İdentifikasiya Nömrəsi)
def generate_mock_fin() -> str:
    """Generate a mock FIN code (7 characters).

    Format: DXXXXXXX where:
    - D: 1-9 (first digit)
    - X: Random alphanumeric (avoiding similar chars)

    Example: 5XYZ123, 2ABC456
    """
    first_digit = random.randint(1, 9)
    rest = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789") for _ in range(6))
    return f"{first_digit}{rest}"


def generate_mock_phone() -> str:
    """Generate a mock Azerbaijani phone number.

    Format: +994XX-XXX-XXXX (using real Baku area code 12)
    """
    area_code = 12  # Baku area code
    exchange = random.randint(100, 999)
    line = random.randint(1000, 9999)
    return f"+994{area_code}{exchange}{line}"


class ALEMPersona:
    """Synthetic Agricultural Persona for a farmer.

    Generated on first login if not already present in database.
    Provides rich context for personalized recommendations.
    """

    def __init__(
        self,
        user_id: str,
        full_name: str,
        email: str,
        fin_code: str | None = None,
        phone: str | None = None,
        region: str | None = None,
        crop_type: str | None = None,
        total_area_ha: float | None = None,
        experience_level: str | None = None,
        ektis_verified: bool = True,
        created_at: datetime | None = None,
    ):
        """Initialize ALEM Persona.

        Args:
            user_id: Unique user identifier (Google 'sub' or mygov ID)
            full_name: User's full name from OAuth
            email: User's email
            fin_code: Optional FIN (auto-generated if None)
            phone: Optional phone (auto-generated if None)
            region: Optional region (randomly selected if None)
            crop_type: Optional primary crop (randomly selected if None)
            total_area_ha: Optional farm size (randomly generated if None)
            experience_level: Optional farmer experience (randomly selected if None)
            ektis_verified: Whether persona is verified in EKTIS (default True for demo)
            created_at: Timestamp (auto-set to now if None)
        """
        self.user_id = user_id
        self.full_name = full_name
        self.email = email
        self.fin_code = fin_code or generate_mock_fin()
        self.phone = phone or generate_mock_phone()
        self.region = region or random.choice(AZERBAIJANI_REGIONS)
        self.crop_type = crop_type or random.choice(list(AZERBAIJANI_CROPS.keys()))
        self.experience_level = experience_level or random.choice(FARMER_EXPERIENCE)

        # Farm size distribution favors medium farms (most common)
        size_dist = random.choices(
            ["small", "medium", "large"],
            weights=[20, 60, 20],  # 20% small, 60% medium, 20% large
            k=1,
        )[0]
        min_ha, max_ha = FARM_SIZE_RANGES[size_dist]
        self.total_area_ha = total_area_ha or round(random.uniform(min_ha, max_ha), 1)

        self.ektis_verified = ektis_verified
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert persona to dictionary for JSON serialization.

        Useful for:
        - Storing in Chainlit session
        - Sending to LangGraph agent
        - Displaying in Langfuse metadata
        """
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "fin_code": self.fin_code,
            "phone": self.phone,
            "region": self.region,
            "crop_type": self.crop_type,
            "crop_name_en": AZERBAIJANI_CROPS.get(self.crop_type, self.crop_type),
            "total_area_ha": self.total_area_ha,
            "experience_level": self.experience_level,
            "ektis_verified": self.ektis_verified,
            "created_at": self.created_at.isoformat(),
        }

    def to_sidebar_display(self) -> str:
        """Format persona for Chainlit sidebar display.

        Returns a markdown-formatted string showing:
        - FIN Code (verified)
        - Region
        - Primary Crop
        - Farm Size
        - Experience Level
        """
        experience_emoji = {
            "novice": "🌱",
            "intermediate": "🌿",
            "expert": "🌾",
        }
        emoji = experience_emoji.get(self.experience_level, "🌿")

        crop_en = AZERBAIJANI_CROPS.get(self.crop_type, self.crop_type)

        return (
            f"**🔐 ALEM Təsdiqlənmiş Profil**\n\n"
            f"**FIN Kodu:** {self.fin_code}\n"
            f"**Bölgə:** {self.region}\n"
            f"**Əsas Məhsul:** {self.crop_type} ({crop_en})\n"
            f"**Sahə:** {self.total_area_ha} ha\n"
            f"**Təcrübə:** {emoji} {self.experience_level}\n"
            f"**EKTIS Statusu:** {'✓ Təsdiqlənmiş' if self.ektis_verified else '⏳ Gözlənilir'}"
        )


class PersonaProvisioner:
    """JIT Provisioning Engine — Auto-generates personas on first login.

    This is the core logic that bridges the gap between:
    - Minimal Google OAuth claims
    - Rich agricultural context required for ALEM demonstrations
    """

    @staticmethod
    def provision_from_oauth(
        user_id: str,
        oauth_claims: dict[str, Any],
        existing_persona: ALEMPersona | None = None,
    ) -> ALEMPersona:
        """Generate or return ALEM persona from OAuth claims.

        Args:
            user_id: Unique identifier (typically Google 'sub')
            oauth_claims: Dict with 'name', 'email', etc. from OAuth provider
            existing_persona: If persona already exists, return it unchanged

        Returns:
            ALEMPersona instance (new or existing)

        Logic:
            If persona exists → return unchanged
            If persona missing → generate synthetic one from Google claims
        """
        if existing_persona:
            logger.info(
                "persona_already_exists",
                user_id=user_id,
                fin_code=existing_persona.fin_code,
            )
            return existing_persona

        # Extract available data from OAuth
        full_name = oauth_claims.get("name", "Unknown Farmer")
        email = oauth_claims.get("email", f"{user_id}@gmail.com")

        # Generate new persona
        persona = ALEMPersona(
            user_id=user_id,
            full_name=full_name,
            email=email,
        )

        logger.info(
            "persona_provisioned_jit",
            user_id=user_id,
            fin_code=persona.fin_code,
            region=persona.region,
            crop_type=persona.crop_type,
            farm_size_ha=persona.total_area_ha,
            experience_level=persona.experience_level,
        )

        return persona

    @staticmethod
    def provision_from_mygov(
        user_id: str,
        mygov_claims: dict[str, Any],
    ) -> ALEMPersona:
        """Generate persona from mygov ID claims (future integration).

        When mygov ID is available, extract actual government data:
        - FIN code (real, not mocked)
        - Phone (real)
        - Region (from address or registration)
        - EKTIS data (from government database)

        For now, this is a placeholder that shows the intended flow.
        """
        fin_code = mygov_claims.get("fin")  # Real FIN from government
        phone = mygov_claims.get("phone")  # Real phone from government
        full_name = mygov_claims.get("name")
        email = mygov_claims.get("email")

        # Region/crop could come from EKTIS lookup using FIN
        region = mygov_claims.get("region")  # Or lookup from EKTIS
        crop_type = mygov_claims.get("crop")  # Or lookup from EKTIS
        total_area_ha = mygov_claims.get("farm_area_ha")  # Or lookup from EKTIS

        persona = ALEMPersona(
            user_id=user_id,
            full_name=full_name,
            email=email,
            fin_code=fin_code,
            phone=phone,
            region=region,
            crop_type=crop_type,
            total_area_ha=total_area_ha,
            ektis_verified=True,  # Explicitly verified by government
        )

        logger.info(
            "persona_provisioned_from_mygov",
            user_id=user_id,
            fin_code=fin_code,
            ektis_verified=True,
        )

        return persona

    @staticmethod
    def generate_gold_standard_scenario(scenario_name: str) -> ALEMPersona:
        """Generate a pre-configured "Gold Standard" persona for demos.

        These are high-quality farmer scenarios used in video calls to show
        how ALEM adapts advice based on farmer profile.

        Examples:
            - "cotton_farmer_sabirabad" → Large cotton farmer, 40ha, expert
            - "apple_grower_quba" → Medium apple grower, 8ha, intermediate
            - "novice_vegetables_gence" → Small vegetable grower, 3ha, novice
        """
        scenarios = {
            "cotton_farmer_sabirabad": {
                "full_name": "Həsən Quliyev",
                "region": "Sabirabad",
                "crop_type": "Pambıq",
                "total_area_ha": 42.5,
                "experience_level": "expert",
            },
            "apple_grower_quba": {
                "full_name": "Aynur Əliyeva",
                "region": "Quba",
                "crop_type": "Alma",
                "total_area_ha": 8.3,
                "experience_level": "intermediate",
            },
            "novice_vegetables_gence": {
                "full_name": "Vasif Hüseynov",
                "region": "Gəncə",
                "crop_type": "Pomidor",
                "total_area_ha": 3.2,
                "experience_level": "novice",
            },
            "wheat_farmer_aran": {
                "full_name": "Zeynəb Mustafayeva",
                "region": "Aran",
                "crop_type": "Buğda",
                "total_area_ha": 25.0,
                "experience_level": "intermediate",
            },
            "hazelnut_farmer_shaki": {
                "full_name": "Rəfiq Məhərrəmov",
                "region": "Şəki",
                "crop_type": "Fındıq",
                "total_area_ha": 15.7,
                "experience_level": "expert",
            },
        }

        if scenario_name not in scenarios:
            raise ValueError(
                f"Unknown scenario: {scenario_name}. Available: {list(scenarios.keys())}"
            )

        config = scenarios[scenario_name]
        persona = ALEMPersona(
            user_id=f"demo_{scenario_name}",
            full_name=config["full_name"],
            email=f"demo_{scenario_name}@zekalab.info",
            fin_code=generate_mock_fin(),  # Still mock for demo
            phone=generate_mock_phone(),
            region=config["region"],
            crop_type=config["crop_type"],
            total_area_ha=config["total_area_ha"],
            experience_level=config["experience_level"],
            ektis_verified=True,
        )

        logger.info(
            "gold_standard_scenario_loaded",
            scenario=scenario_name,
            farmer_name=persona.full_name,
            region=persona.region,
        )

        return persona
