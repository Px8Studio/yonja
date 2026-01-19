"""Poetry script: Run database migrations."""
import subprocess
import sys

def main():
    """Run Alembic migrations."""
    sys.exit(subprocess.call(["alembic", "upgrade", "head"]))

if __name__ == "__main__":
    main()
