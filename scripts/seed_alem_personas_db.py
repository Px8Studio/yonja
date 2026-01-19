#!/usr/bin/env python
# scripts/seed_alem_personas_db.py
"""Seed ALEM Personas directly to PostgreSQL database.

This script creates 5 demo personas in the alem_personas table for testing
and video demonstrations. Unlike seed_alem_personas.py, this version writes
directly to the database without requiring a Chainlit session.

Usage:
    python scripts/seed_alem_personas_db.py
    
    Or with custom database URL:
    DATABASE_URL="postgresql://..." python scripts/seed_alem_personas_db.py
"""

import sys
import uuid
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "demo-ui"))
sys.path.insert(0, str(project_root / "src"))

from alem_persona import PersonaProvisioner
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
)

# Gold Standard Scenarios
DEMO_SCENARIOS = [
    "cotton_farmer_sabirabad",
    "apple_grower_quba",
    "novice_vegetables_gence",
    "wheat_farmer_aran",
    "hazelnut_farmer_shaki",
]


async def seed_personas_to_db():
    """Generate and save demo personas to database."""
    print("\n" + "=" * 70)
    print("🌾 ALEM DEMO PERSONAS — Seeding to Database")
    print("=" * 70 + "\n")
    print(f"📊 Database: {DATABASE_URL.split('@')[-1]}\n")
    
    # Create async engine
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    seeded_count = 0
    
    async with async_session() as session:
        for scenario in DEMO_SCENARIOS:
            try:
                print(f"🌿 Generating: {scenario}")
                
                # Generate persona
                persona = PersonaProvisioner.generate_gold_standard_scenario(scenario)
                persona_dict = persona.to_dict()
                
                # Generate UUIDs
                persona_id = str(uuid.uuid4())
                # Demo personas don't need to be linked to Chainlit users
                chainlit_user_id = None  # Nullable for demo personas
                
                # Insert into database
                await session.execute(
                    text("""
                        INSERT INTO alem_personas (
                            alem_persona_id, chainlit_user_id, email, user_profile_id,
                            full_name, fin_code, phone, region, crop_type, total_area_ha,
                            experience_level, ektis_verified, data_source, created_at, last_login_at
                        ) VALUES (
                            :persona_id, :user_id, :email, :profile_id,
                            :name, :fin, :phone, :region, :crop, :area,
                            :exp, :verified, :source, :created, :login
                        )
                        ON CONFLICT (email) DO UPDATE SET
                            last_login_at = :login,
                            updated_at = CURRENT_TIMESTAMP
                    """),
                    {
                        'persona_id': persona_id,
                        'user_id': chainlit_user_id,
                        'email': persona.email,
                        'profile_id': None,  # Not linked to user_profiles
                        'name': persona.full_name,
                        'fin': persona.fin_code,
                        'phone': persona.phone,
                        'region': persona.region,
                        'crop': persona.crop_type,
                        'area': persona.total_area_ha,
                        'exp': persona.experience_level,
                        'verified': True,  # Demo personas are "verified"
                        'source': 'gold_standard',
                        'created': datetime.now(timezone.utc),
                        'login': datetime.now(timezone.utc),
                    }
                )
                
                print(f"   ✅ {persona.full_name} ({persona.email})")
                print(f"      📍 {persona.region} | 🌾 {persona.crop_type} | 📏 {persona.total_area_ha} ha")
                seeded_count += 1
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Commit all inserts
        await session.commit()
    
    await engine.dispose()
    
    print("\n" + "=" * 70)
    print(f"✅ Successfully seeded {seeded_count}/{len(DEMO_SCENARIOS)} personas!")
    print("=" * 70)
    
    # Print verification query
    print("\n📋 VERIFY:")
    print("docker exec yonca-postgres psql -U yonca -d yonca -c \"\"\"")
    print("  SELECT email, full_name, region, crop_type, total_area_ha")
    print("  FROM alem_personas WHERE data_source = 'gold_standard';")
    print("\"\"\"")
    print()


if __name__ == "__main__":
    asyncio.run(seed_personas_to_db())
