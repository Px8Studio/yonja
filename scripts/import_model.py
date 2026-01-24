#!/usr/bin/env python3
"""
Import GGUF models into Ollama for local development.

This script imports GGUF model files (e.g., from Hugging Face) into Ollama,
making them available for use with the Yonca AI application.

Usage:
    # Import ATLLaMA model (default)
    python scripts/import_model.py

    # Import specific model
    python scripts/import_model.py --name mymodel --path models/mymodel.gguf

    # Import into Docker container
    python scripts/import_model.py --docker
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Try to import ollama, but make it optional for Docker mode
try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# Default system prompt for Azerbaijani farming assistant
DEFAULT_SYSTEM_PROMPT = """Sən Azərbaycan fermerlərə kömək edən süni intellekt köməkçisisən.
Sualları Azərbaycan dilində cavablandır. Əkin, torpaq, iqlim və kənd təsərrüfatı mövzularında məlumat ver."""


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def import_gguf_local(
    model_name: str,
    gguf_path: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> bool:
    """Import GGUF model using local Ollama Python client."""
    if not OLLAMA_AVAILABLE:
        print("❌ Ollama Python package not installed.")
        print("   Install with: pip install ollama")
        return False

    # Get absolute path for Windows compatibility
    abs_path = os.path.abspath(gguf_path)

    if not os.path.exists(abs_path):
        print(f"❌ GGUF file not found: {abs_path}")
        return False

    # Define the Modelfile content
    modelfile = f"""FROM {abs_path}
SYSTEM "{system_prompt}"
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
"""

    print(f"📦 Importing '{model_name}' from {abs_path}...")
    try:
        ollama.create(model=model_name, modelfile=modelfile)
        print(f"✅ Model '{model_name}' is ready!")
        return True
    except Exception as e:
        print(f"❌ Failed to import model: {e}")
        return False


def import_gguf_docker(
    model_name: str,
    gguf_path: str,
    container_name: str = "alim-ollama",
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> bool:
    """Import GGUF model into Ollama running in Docker container.

    This requires the GGUF file to be mounted into the container.
    The docker-compose.local.yml should mount ./models:/app/models
    """
    # Check if container is running
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    if container_name not in result.stdout:
        print(f"❌ Container '{container_name}' is not running.")
        print("   Start with: docker-compose -f docker-compose.local.yml up -d")
        return False

    # Path inside the container (assuming ./models is mounted to /app/models)
    container_gguf_path = f"/app/models/{Path(gguf_path).name}"

    # Create a temporary Modelfile
    modelfile_content = f"""FROM {container_gguf_path}
SYSTEM "{system_prompt}"
PARAMETER temperature 0.7
PARAMETER num_ctx 4096
"""

    # Write Modelfile to a temp location and copy to container
    temp_modelfile = get_project_root() / "models" / f"Modelfile.{model_name}"
    temp_modelfile.write_text(modelfile_content)

    print(f"📦 Importing '{model_name}' into Docker container...")

    try:
        # Copy Modelfile to container
        subprocess.run(
            ["docker", "cp", str(temp_modelfile), f"{container_name}:/tmp/Modelfile"],
            check=True,
        )

        # Create model in container
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "ollama",
                "create",
                model_name,
                "-f",
                "/tmp/Modelfile",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ Model '{model_name}' imported successfully!")
            return True
        else:
            print(f"❌ Failed to import model: {result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Docker command failed: {e}")
        return False
    finally:
        # Cleanup temp file
        if temp_modelfile.exists():
            temp_modelfile.unlink()


def list_models_docker(container_name: str = "alim-ollama") -> None:
    """List models available in the Docker container."""
    result = subprocess.run(
        ["docker", "exec", container_name, "ollama", "list"],
        capture_output=True,
        text=True,
    )
    print("\n📋 Available models in container:")
    print(result.stdout if result.returncode == 0 else "❌ Could not list models")


def list_models_local() -> None:
    """List models available locally."""
    if not OLLAMA_AVAILABLE:
        print("❌ Ollama Python package not installed")
        return

    try:
        models = ollama.list()
        print("\n📋 Available local models:")
        for model in models.get("models", []):
            print(f"  - {model['name']}")
    except Exception as e:
        print(f"❌ Could not list models: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Import GGUF models into Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Import ATLLaMA (default)
    python scripts/import_model.py

    # Import into Docker container
    python scripts/import_model.py --docker

    # Import custom model
    python scripts/import_model.py --name mymodel --path models/custom.gguf

    # List available models
    python scripts/import_model.py --list
""",
    )
    parser.add_argument(
        "--name",
        default="atllama",
        help="Name for the imported model (default: atllama)",
    )
    parser.add_argument(
        "--path",
        default="models/atllama.v3.5.Q4_K_M.gguf",
        help="Path to the GGUF file",
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Import into Docker container instead of local Ollama",
    )
    parser.add_argument(
        "--container",
        default="alim-ollama",
        help="Docker container name (default: alim-ollama)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models and exit",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_SYSTEM_PROMPT,
        help="System prompt for the model",
    )

    args = parser.parse_args()

    # Change to project root
    os.chdir(get_project_root())

    if args.list:
        if args.docker:
            list_models_docker(args.container)
        else:
            list_models_local()
        return

    # Import the model
    if args.docker:
        success = import_gguf_docker(
            args.name,
            args.path,
            args.container,
            args.system_prompt,
        )
    else:
        success = import_gguf_local(
            args.name,
            args.path,
            args.system_prompt,
        )

    if success:
        print("\n🎉 You can now use this model:")
        if args.docker:
            print(f"   docker exec -it {args.container} ollama run {args.name}")
        else:
            print(f"   ollama run {args.name}")
        print(f"\n   Or set ALIM_OLLAMA_MODEL={args.name} in your .env file")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
