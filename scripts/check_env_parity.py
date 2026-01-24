#!/usr/bin/env python
"""
Environment Parity Checker for ALIM.
Ensures that .env and .env.example stay in sync with the codebase configuration (src/yonca/config.py).
"""

import sys
from pathlib import Path

from dotenv import dotenv_values

# Add src to path so we can import alim
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from alim.config import Settings
except ImportError as e:
    print(f"❌ Could not import settings: {e}")
    sys.exit(1)


def check_parity():
    # 1. Get expected fields from Pydantic model
    # Convert field names to env vars (e.g. database_url -> ALIM_DATABASE_URL)
    prefix = Settings.model_config.get("env_prefix", "").upper()
    expected_vars = {f"{prefix}{name.upper()}" for name in Settings.model_fields.keys()}

    print(f"ℹ️  Codebase expects {len(expected_vars)} variables (Prefix: {prefix})")

    # 2. Check .env.example
    example_path = Path(".env.example")
    if example_path.exists():
        example_vars = set(dotenv_values(example_path).keys())
        missing_in_example = expected_vars - example_vars
        # Optional: We don't necessarily error on extra vars in example (comments etc), but good to know

        if missing_in_example:
            print(f"\n❌ .env.example is missing {len(missing_in_example)} required variables:")
            for var in sorted(missing_in_example):
                print(f"   - {var}")
            sys.exit(1)
        else:
            print("✅ .env.example is complete.")
    else:
        print("⚠️  .env.example not found.")

    # 3. Check local .env (if exists)
    env_path = Path(".env")
    if env_path.exists():
        local_vars = set(dotenv_values(env_path).keys())

        # Check for legacy prefixes
        legacy_vars = [v for v in local_vars if v.startswith("YONCA_")]
        if legacy_vars:
            print(
                f"\n⚠️  Found {len(legacy_vars)} legacy 'YONCA_' variables in .env. Please rename to '{prefix}'."
            )

        # Check for missing required vars (that don't have defaults)
        # Note: Pydantic handles defaults, so we only *really* care if the app crashes,
        # but for clean config we can check valid keys.

        print("✅ .env check complete (runtime validation handled by Pydantic).")
    else:
        print("ℹ️  No local .env found (using defaults).")


if __name__ == "__main__":
    check_parity()
