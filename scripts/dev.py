"""Poetry script: Start development server."""
import subprocess
import sys


def main():
    """Start FastAPI development server with auto-reload."""
    sys.exit(
        subprocess.call(
            ["uvicorn", "alim.api.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
        )
    )


if __name__ == "__main__":
    main()
