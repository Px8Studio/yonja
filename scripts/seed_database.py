#!/usr/bin/env python
# scripts/seed_database.py
"""Seed database with synthetic farm profiles.

Generates 5 distinct user personas with 1-5 farms each:
1. Novice Farmer - 1 farm, needs detailed guidance
2. Experienced Holder - 2 farms, prefers brief advice
3. Commercial Operator - 4 farms, data-driven decisions
4. Traditional Farmer - 1 farm, respects local methods
5. Diversified Owner - 3 farms, mixed crop + livestock

Each farm has:
- 1-3 parcels with GPS coordinates
- Active sowing declarations
- Historical crop rotation logs (3 years)
- NDVI time series (synthetic satellite data)

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --reset  # Clear and reseed
"""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from faker import Faker

from yonca.data.database import Base, engine, get_db_session
from yonca.data.models import (
    CropRotationLog,
    FarmProfile,
    NDVIReading,
    Parcel,
    SowingDeclaration,
    UserProfile,
)
from yonca.data.models.farm import FarmType, Region
from yonca.data.models.ndvi import HealthStatus
from yonca.data.models.parcel import IrrigationType, SoilType
from yonca.data.models.sowing import CropType, DeclarationStatus
from yonca.data.models.user import EducationLevel, ExperienceLevel, NotificationPreference
from yonca.data.providers.azerbaijani import AzerbaijaniAgrarianProvider


# Initialize Faker with Azerbaijani provider
fake = Faker("az_AZ")
fake.add_provider(AzerbaijaniAgrarianProvider)


# ===== Persona Definitions =====

PERSONAS = [
    {
        "index": 1,
        "type": "novice",
        "name": "Novice Farmer",
        "description": "New to farming, needs detailed guidance",
        "experience_level": ExperienceLevel.NOVICE,
        "farming_years": 2,
        "education_level": EducationLevel.SECONDARY,
        "receives_subsidies": True,
        "notification_pref": NotificationPreference.SMS,
        "region": "Aran",
        "farm_count": 1,
        "farm_types": [FarmType.CROP],
    },
    {
        "index": 2,
        "type": "experienced",
        "name": "Experienced Holder",
        "description": "15 years experience, prefers brief advice",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "farming_years": 15,
        "education_level": EducationLevel.TECHNICAL,
        "receives_subsidies": True,
        "notification_pref": NotificationPreference.BOTH,
        "region": "Quba-Qusar",
        "farm_count": 2,
        "farm_types": [FarmType.ORCHARD, FarmType.CROP],
    },
    {
        "index": 3,
        "type": "commercial",
        "name": "Commercial Operator",
        "description": "Data-driven, large operations",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "farming_years": 10,
        "education_level": EducationLevel.UNIVERSITY,
        "receives_subsidies": True,
        "notification_pref": NotificationPreference.APP,
        "region": "Mil-Muğan",
        "farm_count": 4,
        "farm_types": [FarmType.CROP, FarmType.CROP, FarmType.ORCHARD, FarmType.MIXED],
    },
    {
        "index": 4,
        "type": "traditional",
        "name": "Traditional Farmer",
        "description": "30 years experience, respects local methods",
        "experience_level": ExperienceLevel.EXPERT,
        "farming_years": 30,
        "education_level": EducationLevel.PRIMARY,
        "receives_subsidies": False,
        "notification_pref": NotificationPreference.SMS,
        "region": "Şəki-Zaqatala",
        "farm_count": 1,
        "farm_types": [FarmType.LIVESTOCK],
    },
    {
        "index": 5,
        "type": "diversified",
        "name": "Diversified Owner",
        "description": "Multiple farm types, adaptable",
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "farming_years": 8,
        "education_level": EducationLevel.TECHNICAL,
        "receives_subsidies": True,
        "notification_pref": NotificationPreference.BOTH,
        "region": "Lənkəran",
        "farm_count": 3,
        "farm_types": [FarmType.MIXED, FarmType.ORCHARD, FarmType.CROP],
    },
]


# ===== Region to Crops Mapping =====

REGION_CROPS = {
    "Aran": [CropType.WINTER_WHEAT, CropType.COTTON, CropType.CORN],
    "Quba-Qusar": [CropType.APPLE, CropType.PEAR, CropType.GRAPE],
    "Şəki-Zaqatala": [CropType.HAZELNUT, CropType.TOBACCO, CropType.WALNUT],
    "Mil-Muğan": [CropType.COTTON, CropType.WINTER_WHEAT, CropType.SUNFLOWER],
    "Lənkəran": [CropType.TOMATO, CropType.CUCUMBER, CropType.TEA],
    "Abşeron": [CropType.GRAPE, CropType.TOMATO, CropType.CUCUMBER],
    "Gəncə-Daşkəsən": [CropType.GRAPE, CropType.WINTER_WHEAT, CropType.POTATO],
}

FARM_TYPE_TO_REGION = {
    FarmType.CROP: ["Aran", "Mil-Muğan", "Gəncə-Daşkəsən"],
    FarmType.ORCHARD: ["Quba-Qusar", "Şəki-Zaqatala", "Lənkəran"],
    FarmType.LIVESTOCK: ["Şəki-Zaqatala"],
    FarmType.MIXED: ["Lənkəran", "Abşeron"],
}


async def create_user(session, persona: dict) -> UserProfile:
    """Create a user profile from persona definition."""
    user = UserProfile(
        user_id=fake.user_id(persona["index"]),
        full_name_masked=fake.masked_name(persona["index"]),
        phone_hash=fake.phone_hash(),
        region_code=fake.region_code(persona["region"]),
        experience_level=persona["experience_level"],
        farming_years=persona["farming_years"],
        education_level=persona["education_level"],
        language_pref="az_AZ",
        preferred_units="metric",
        receives_subsidies=persona["receives_subsidies"],
        notification_pref=persona["notification_pref"],
    )
    session.add(user)
    return user


async def create_farm(
    session,
    user_id: str,
    user_index: int,
    farm_index: int,
    farm_type: FarmType,
    is_primary: bool,
) -> FarmProfile:
    """Create a farm profile with realistic attributes."""
    # Pick region based on farm type
    possible_regions = FARM_TYPE_TO_REGION.get(farm_type, ["Aran"])
    region_name = fake.random_element(possible_regions)
    region = Region(region_name)
    
    # Generate area based on farm type
    area_ranges = {
        FarmType.CROP: (5.0, 30.0),
        FarmType.ORCHARD: (1.0, 8.0),
        FarmType.LIVESTOCK: (2.0, 15.0),
        FarmType.MIXED: (3.0, 20.0),
    }
    area_range = area_ranges.get(farm_type, (3.0, 15.0))
    total_area = round(fake.pyfloat(min_value=area_range[0], max_value=area_range[1]), 2)
    
    # Primary activity
    crops = REGION_CROPS.get(region_name, [CropType.WINTER_WHEAT])
    primary_activity = fake.random_element([c.value for c in crops])
    
    farm = FarmProfile(
        farm_id=fake.farm_id(user_index, farm_index),
        user_id=user_id,
        farm_name=fake.farm_name(),
        farm_type=farm_type,
        region=region,
        total_area_ha=total_area,
        primary_activity=primary_activity,
        is_primary=is_primary,
        is_active=True,
    )
    session.add(farm)
    return farm


async def create_parcel(
    session,
    farm: FarmProfile,
    parcel_index: int,
    area_ha: float,
) -> Parcel:
    """Create a parcel within a farm."""
    region_name = farm.region.value
    lat, lon = fake.coordinates(region_name, offset_km=20.0)
    
    # Soil type weighted by region (simplified)
    soil_types = [SoilType.LOAM, SoilType.CLAY, SoilType.ALLUVIAL, SoilType.CHERNOZEM]
    soil = fake.random_element(soil_types)
    
    # Irrigation type based on farm type
    if farm.farm_type in [FarmType.ORCHARD, FarmType.MIXED]:
        irrigation = fake.random_element([IrrigationType.DRIP, IrrigationType.SPRINKLER])
    elif farm.farm_type == FarmType.CROP:
        irrigation = fake.random_element([IrrigationType.PIVOT, IrrigationType.FURROW, IrrigationType.FLOOD])
    else:
        irrigation = IrrigationType.RAINFED
    
    parcel = Parcel(
        parcel_id=fake.parcel_id(region_name),
        farm_id=farm.farm_id,
        latitude=lat,
        longitude=lon,
        area_hectares=area_ha,
        soil_type=soil,
        irrigation_type=irrigation,
        elevation_m=fake.pyfloat(min_value=50, max_value=1500) if farm.region in [Region.SHEKI_ZAQATALA, Region.QUBA_QUSAR] else None,
    )
    session.add(parcel)
    return parcel


async def create_sowing_declaration(
    session,
    parcel: Parcel,
    region_name: str,
    year: int,
) -> SowingDeclaration:
    """Create a sowing declaration for a parcel."""
    crops = REGION_CROPS.get(region_name, [CropType.WINTER_WHEAT])
    crop = fake.random_element(crops)
    
    # Determine sowing date based on crop
    if crop in [CropType.WINTER_WHEAT, CropType.BARLEY]:
        sowing_date = date(year - 1, 10, fake.random_int(1, 31))
    elif crop in [CropType.COTTON, CropType.CORN, CropType.SUNFLOWER]:
        sowing_date = date(year, 4, fake.random_int(1, 30))
    elif crop in [CropType.TOMATO, CropType.CUCUMBER, CropType.PEPPER]:
        sowing_date = date(year, 3, fake.random_int(1, 31))
    else:
        sowing_date = date(year, 3, fake.random_int(1, 31))
    
    # Expected harvest (approx 4-6 months later)
    harvest_days = fake.random_int(120, 200)
    expected_harvest = sowing_date + timedelta(days=harvest_days)
    
    declaration = SowingDeclaration(
        declaration_id=fake.declaration_id(year),
        parcel_id=parcel.parcel_id,
        crop_type=crop,
        sowing_date=sowing_date,
        expected_harvest_date=expected_harvest,
        status=DeclarationStatus.CONFIRMED,
        expected_yield_tons=round(fake.yield_tons_per_ha(crop.value) * parcel.area_hectares, 2),
        season_year=year,
    )
    session.add(declaration)
    return declaration


async def create_crop_rotation(
    session,
    parcel: Parcel,
    region_name: str,
    year: int,
) -> CropRotationLog:
    """Create historical crop rotation log."""
    crops = REGION_CROPS.get(region_name, [CropType.WINTER_WHEAT])
    crop = fake.random_element(crops)
    
    yield_per_ha = fake.yield_tons_per_ha(crop.value)
    total_yield = round(yield_per_ha * parcel.area_hectares, 2)
    
    rotation = CropRotationLog(
        log_id=fake.crop_rotation_id(parcel.parcel_id, year),
        parcel_id=parcel.parcel_id,
        year=year,
        crop=crop.value,
        yield_tons_per_ha=yield_per_ha,
        total_yield_tons=total_yield,
        quality_grade=fake.random_element(["A", "B", "B", "C"]),
    )
    session.add(rotation)
    return rotation


async def create_ndvi_readings(
    session,
    parcel: Parcel,
    crop_type: CropType,
    sowing_date: date,
) -> list[NDVIReading]:
    """Create NDVI time series for a parcel."""
    readings = []
    
    # Generate synthetic NDVI series
    ndvi_series = fake.ndvi_series(
        crop=crop_type.value,
        start_date=sowing_date,
        days=270,
        interval_days=10,
    )
    
    for i, data in enumerate(ndvi_series):
        reading = NDVIReading(
            reading_id=f"NDVI-{parcel.parcel_id.replace('AZ-', '')}-{data['date'].strftime('%Y%m%d')}",
            parcel_id=parcel.parcel_id,
            reading_date=data["date"],
            ndvi_value=data["ndvi"],
            health_status=HealthStatus(data["health_status"]),
            cloud_cover_percent=fake.pyfloat(min_value=0, max_value=30),
            data_source="synthetic",
        )
        readings.append(reading)
    
    session.add_all(readings)
    return readings


async def seed_database(reset: bool = False):
    """Main seeding function.
    
    Args:
        reset: If True, drop and recreate all tables before seeding
    """
    print("🌱 Starting database seeding...")
    
    if reset:
        print("⚠️  Resetting database (dropping all tables)...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database reset complete")
    
    async with get_db_session() as session:
        current_year = date.today().year
        
        for persona in PERSONAS:
            print(f"\n👤 Creating {persona['name']} (syn_user_{persona['index']:03d})")
            
            # Create user
            user = await create_user(session, persona)
            print(f"   ✅ User: {user.user_id}")
            
            # Create farms
            for farm_idx, farm_type in enumerate(persona["farm_types"]):
                is_primary = (farm_idx == 0)
                farm = await create_farm(
                    session,
                    user_id=user.user_id,
                    user_index=persona["index"],
                    farm_index=farm_idx,
                    farm_type=farm_type,
                    is_primary=is_primary,
                )
                print(f"   🏠 Farm: {farm.farm_id} ({farm.farm_type.value}, {farm.region.value}, {farm.total_area_ha}ha)")
                
                # Determine parcel count (1-3 per farm)
                parcel_count = min(3, max(1, int(farm.total_area_ha / 5) + 1))
                remaining_area = farm.total_area_ha
                
                for parcel_idx in range(parcel_count):
                    # Distribute area among parcels
                    if parcel_idx == parcel_count - 1:
                        parcel_area = remaining_area
                    else:
                        parcel_area = round(remaining_area / (parcel_count - parcel_idx) * fake.pyfloat(min_value=0.7, max_value=1.3), 2)
                        parcel_area = min(parcel_area, remaining_area - 0.5 * (parcel_count - parcel_idx - 1))
                    remaining_area -= parcel_area
                    
                    parcel = await create_parcel(session, farm, parcel_idx, parcel_area)
                    print(f"      📍 Parcel: {parcel.parcel_id} ({parcel_area}ha)")
                    
                    # Create current year sowing declaration
                    declaration = await create_sowing_declaration(
                        session,
                        parcel,
                        farm.region.value,
                        current_year,
                    )
                    print(f"         🌾 Crop: {declaration.crop_type.value}")
                    
                    # Create historical crop rotation (3 years)
                    for year in range(current_year - 3, current_year):
                        await create_crop_rotation(session, parcel, farm.region.value, year)
                    print(f"         📊 Rotation: {current_year - 3}-{current_year - 1}")
                    
                    # Create NDVI readings
                    ndvi_readings = await create_ndvi_readings(
                        session,
                        parcel,
                        declaration.crop_type,
                        declaration.sowing_date,
                    )
                    print(f"         🛰️  NDVI: {len(ndvi_readings)} readings")
        
        # Commit all changes
        await session.commit()
    
    print("\n" + "=" * 50)
    print("✅ Database seeding complete!")
    print("=" * 50)
    
    # Print summary
    async with get_db_session() as session:
        from sqlalchemy import func, select
        
        user_count = (await session.execute(select(func.count(UserProfile.user_id)))).scalar()
        farm_count = (await session.execute(select(func.count(FarmProfile.farm_id)))).scalar()
        parcel_count = (await session.execute(select(func.count(Parcel.parcel_id)))).scalar()
        declaration_count = (await session.execute(select(func.count(SowingDeclaration.declaration_id)))).scalar()
        rotation_count = (await session.execute(select(func.count(CropRotationLog.log_id)))).scalar()
        ndvi_count = (await session.execute(select(func.count(NDVIReading.reading_id)))).scalar()
        
        print(f"""
📊 Summary:
   👤 Users:        {user_count}
   🏠 Farms:        {farm_count}
   📍 Parcels:      {parcel_count}
   🌾 Declarations: {declaration_count}
   📊 Rotations:    {rotation_count}
   🛰️  NDVI:        {ndvi_count}
""")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed database with synthetic data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate tables before seeding")
    args = parser.parse_args()
    
    asyncio.run(seed_database(reset=args.reset))
