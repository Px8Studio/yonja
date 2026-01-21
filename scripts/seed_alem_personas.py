#!/usr/bin/env python
# scripts/seed_alem_personas.py
"""Seed ALEM Demo Personas for Video Call Demonstrations.

This script creates 5 high-quality "Gold Standard" farmer scenarios that can be
used in video demonstrations to show how ALEM adapts its advice based on farmer profile.

Each persona represents a realistic Azerbaijani farming scenario with:
- Authentic Azerbaijani names
- Real agricultural regions in Azerbaijan
- Appropriate crop types for each region
- Realistic farm sizes
- Different experience levels

Usage:
    python scripts/seed_alem_personas.py

    Or with database URL:
    DATABASE_URL="postgresql://..." python scripts/seed_alem_personas.py

    To persist to database:
    python scripts/seed_alem_personas.py --to-db

The script can also be run from Chainlit directly:
    - Go to demo-ui/
    - python -c "from alem_persona import PersonaProvisioner; p = PersonaProvisioner.generate_gold_standard_scenario('cotton_farmer_sabirabad'); print(p.to_dict())"
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "demo-ui"))
sys.path.insert(0, str(project_root / "src"))

from alem_persona import PersonaProvisioner  # noqa: E402

# Database persistence (optional)
DB_AVAILABLE = False
try:
    from alem_persona_db import save_alem_persona_to_db

    DB_AVAILABLE = True
except ImportError:
    pass

# ============================================
# Gold Standard Scenarios for Video Demos
# ============================================

DEMO_SCENARIOS = [
    "cotton_farmer_sabirabad",
    "apple_grower_quba",
    "novice_vegetables_gence",
    "wheat_farmer_aran",
    "hazelnut_farmer_shaki",
]


def seed_all_personas(persist_to_db: bool = False):
    """Generate and print all 5 demo personas.

    These are intended for use in video calls where you show how ALEM
    provides different advice based on the farmer's profile.

    Args:
        persist_to_db: If True, save personas to database
    """
    print("\n" + "=" * 70)
    print("🌾 ALEM DEMO PERSONAS — Gold Standard Scenarios")
    print("=" * 70 + "\n")

    if persist_to_db and not DB_AVAILABLE:
        print("⚠️  Database persistence not available. Install dependencies first.")
        print("    Run: pip install -r requirements.txt")
        persist_to_db = False

    personas_data = []

    for scenario in DEMO_SCENARIOS:
        try:
            print(f"\n🌿 Generating: {scenario}")
            print("-" * 70)

            persona = PersonaProvisioner.generate_gold_standard_scenario(scenario)
            persona_dict = persona.to_dict()
            personas_data.append(persona_dict)

            # Display formatted persona
            print(persona.to_sidebar_display())
            print(f"\n📧 Email: {persona.email}")
            print(f"📞 Phone: {persona.phone}")
            print(f"🌍 Sahə: {persona.total_area_ha} ha")

            # Save to database if requested
            if persist_to_db:
                try:
                    # Generate a mock Chainlit user ID
                    import uuid

                    chainlit_user_id = str(uuid.uuid4())

                    asyncio.run(
                        save_alem_persona_to_db(
                            alem_persona=persona_dict,
                            chainlit_user_id=chainlit_user_id,
                            email=persona.email,
                        )
                    )
                    print(f"✅ Saved to database: {persona.email}")
                except Exception as e:
                    print(f"❌ Database save failed: {e}")

        except Exception as e:
            print(f"❌ Error generating {scenario}: {e}")
            continue

    # Save to JSON for reference
    output_file = Path(__file__).parent / "demo_personas.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(personas_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ Seeded {len(personas_data)} personas successfully!")
    print(f"📁 Saved to: {output_file}")
    if persist_to_db:
        print("💾 Persisted to database: alem_personas table")
    print("=" * 70)

    # Print usage instructions
    print("\n📋 HOW TO USE IN VIDEO DEMO:\n")
    print("1. User logs in with Google OAuth")
    print("2. On first login, ALEM auto-generates a synthetic farmer persona")
    print("3. Each persona includes:")
    print("   - Authentic Azerbaijani name")
    print("   - Real farm location in Azerbaijan")
    print("   - Appropriate crop type for that region")
    print("   - Realistic farm size")
    print("   - Experience level (novice/intermediate/expert)")
    print()
    print("4. ALEM uses this context to provide personalized recommendations")
    print("   - Cotton farmer → irrigation schedules for cotton")
    print("   - Apple grower → pest management for apple orchards")
    print("   - Novice farmer → step-by-step guidance")
    print()
    print("5. When switching to mygov ID:")
    print("   - Replace synthetic persona with real government data")
    print("   - All ALEM logic remains unchanged")
    print("   - Seamless migration!")
    print()


def print_persona_comparison():
    """Print side-by-side comparison of scenarios.

    Useful for understanding the diversity of demo personas.
    """
    print("\n" + "=" * 110)
    print("🔍 DEMO PERSONAS COMPARISON TABLE")
    print("=" * 110 + "\n")

    scenarios = []
    for scenario in DEMO_SCENARIOS:
        persona = PersonaProvisioner.generate_gold_standard_scenario(scenario)
        scenarios.append(persona)

    # Print header
    print(f"{'Name':<20} {'Region':<15} {'Crop':<15} {'Size (ha)':<12} {'Experience':<15}")
    print("-" * 110)

    # Print rows
    for persona in scenarios:
        crop_en = {
            "Pambıq": "Cotton",
            "Alma": "Apple",
            "Pomidor": "Tomato",
            "Buğda": "Wheat",
            "Fındıq": "Hazelnut",
        }.get(persona.crop_type, persona.crop_type)

        print(
            f"{persona.full_name:<20} "
            f"{persona.region:<15} "
            f"{crop_en:<15} "
            f"{persona.total_area_ha:<12.1f} "
            f"{persona.experience_level:<15}"
        )

    print()


def print_persona_for_login(user_name: str) -> str:
    """Generate a persona matching a user's name for quick demo setup.

    Usage:
        python scripts/seed_alem_personas.py --for-login "John Smith"
    """
    # Try to match with a demo scenario (for simplicity)
    # In real usage, you'd want a proper name-to-region mapping
    scenario = DEMO_SCENARIOS[0]  # Default to first scenario

    persona = PersonaProvisioner.generate_gold_standard_scenario(scenario)
    persona.full_name = user_name  # Override with provided name

    print(f"\n🎭 Quick Demo Persona for: {user_name}\n")
    print(persona.to_sidebar_display())
    print(f"\n📧 Email: {persona.email}")
    print(f"📞 Phone: {persona.phone}")
    print(f"\nJSON:\n{json.dumps(persona.to_dict(), ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed ALEM demo personas")
    parser.add_argument(
        "--compare", action="store_true", help="Show side-by-side comparison of all personas"
    )
    parser.add_argument("--for-login", type=str, help="Generate a persona for a specific user name")
    parser.add_argument(
        "--to-db", action="store_true", help="Persist personas to database (requires DATABASE_URL)"
    )

    args = parser.parse_args()

    if args.for_login:
        print_persona_for_login(args.for_login)
    elif args.compare:
        print_persona_comparison()
    else:
        seed_all_personas(persist_to_db=args.to_db)
