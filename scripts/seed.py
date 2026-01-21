"""Poetry script: Seed database with test data."""
import subprocess
import sys
from pathlib import Path


def main():
    """Seed database with test data."""
    script_path = Path(__file__).parent / "seed_database.py"
    sys.exit(subprocess.call(["python", str(script_path)]))


if __name__ == "__main__":
    main()
