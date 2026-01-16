"""
Yonca AI - Startup Manager
Handles Ollama verification and graceful startup.
"""
import subprocess
import sys
import time
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

OLLAMA_API_URL = "http://localhost:11434"
REQUIRED_MODEL = "qwen2.5:7b"


def print_banner():
    """Print Yonca AI startup banner."""
    banner = """
    🌿 YONCA AI - Smart Farm Planning Assistant
    ═══════════════════════════════════════════
    """
    console.print(Panel(banner, style="green", border_style="green"))


def check_ollama_installed() -> bool:
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ollama_running() -> bool:
    """Check if Ollama server is running."""
    try:
        response = httpx.get(f"{OLLAMA_API_URL}/api/tags", timeout=2.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def start_ollama_server() -> bool:
    """Start Ollama server in background."""
    try:
        if sys.platform == "win32":
            # On Windows, Ollama runs as a service - try to start it
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Wait for server to start
        for _ in range(10):
            time.sleep(1)
            if check_ollama_running():
                return True
        return False
    except Exception:
        return False


def check_model_available(model: str = REQUIRED_MODEL) -> bool:
    """Check if the required model is downloaded."""
    try:
        response = httpx.get(f"{OLLAMA_API_URL}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            # Check for exact match or partial match (qwen2.5:7b or qwen2.5:7b-...)
            return any(model in name or name.startswith(model.split(":")[0]) for name in model_names)
        return False
    except Exception:
        return False


def pull_model(model: str = REQUIRED_MODEL) -> bool:
    """Download the required model."""
    console.print(f"\n[yellow]📥 Downloading {model}... (this may take a few minutes)[/yellow]\n")
    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]Error pulling model: {e}[/red]")
        return False


def run_startup_checks(model: str = None) -> dict:
    """
    Run all startup checks and return status.
    
    Returns:
        dict with keys: ollama_installed, ollama_running, model_available, ready
    """
    model = model or REQUIRED_MODEL
    
    status = {
        "ollama_installed": False,
        "ollama_running": False,
        "model_available": False,
        "model_name": model,
        "ready": False,
    }
    
    print_banner()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Check 1: Ollama installed
        task = progress.add_task("Checking Ollama installation...", total=None)
        status["ollama_installed"] = check_ollama_installed()
        progress.remove_task(task)
        
        if not status["ollama_installed"]:
            console.print("[red]❌ Ollama not installed![/red]")
            console.print("\n[yellow]Install Ollama:[/yellow]")
            console.print("  Windows: [cyan]winget install Ollama.Ollama[/cyan]")
            console.print("  macOS:   [cyan]brew install ollama[/cyan]")
            console.print("  Linux:   [cyan]curl -fsSL https://ollama.com/install.sh | sh[/cyan]")
            return status
        
        console.print("[green]✅ Ollama installed[/green]")
        
        # Check 2: Ollama running
        task = progress.add_task("Checking Ollama server...", total=None)
        status["ollama_running"] = check_ollama_running()
        progress.remove_task(task)
        
        if not status["ollama_running"]:
            console.print("[yellow]⏳ Ollama not running, starting...[/yellow]")
            task = progress.add_task("Starting Ollama server...", total=None)
            status["ollama_running"] = start_ollama_server()
            progress.remove_task(task)
            
            if not status["ollama_running"]:
                console.print("[red]❌ Could not start Ollama server![/red]")
                console.print("\n[yellow]Try manually:[/yellow]")
                console.print("  [cyan]ollama serve[/cyan]")
                return status
        
        console.print("[green]✅ Ollama server running[/green]")
        
        # Check 3: Model available
        task = progress.add_task(f"Checking model {model}...", total=None)
        status["model_available"] = check_model_available(model)
        progress.remove_task(task)
        
        if not status["model_available"]:
            console.print(f"[yellow]📥 Model {model} not found, downloading...[/yellow]")
            status["model_available"] = pull_model(model)
            
            if not status["model_available"]:
                console.print(f"[red]❌ Could not download {model}![/red]")
                console.print("\n[yellow]Try manually:[/yellow]")
                console.print(f"  [cyan]ollama pull {model}[/cyan]")
                return status
        
        console.print(f"[green]✅ Model {model} ready[/green]")
    
    status["ready"] = True
    
    # Print summary
    table = Table(title="🌿 Yonca AI Status", border_style="green")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("Ollama", "✅ Running")
    table.add_row("LLM Model", f"✅ {model}")
    table.add_row("API", "🚀 Starting...")
    
    console.print()
    console.print(table)
    console.print()
    
    return status


def main():
    """CLI entry point for startup checks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Yonca AI Startup Manager")
    parser.add_argument(
        "--model", "-m",
        default=REQUIRED_MODEL,
        help=f"LLM model to use (default: {REQUIRED_MODEL})"
    )
    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="Only run checks, don't start the server"
    )
    
    args = parser.parse_args()
    
    status = run_startup_checks(args.model)
    
    if not status["ready"]:
        sys.exit(1)
    
    if args.check_only:
        console.print("[green]All checks passed! Ready to start.[/green]")
        sys.exit(0)
    
    # Start the FastAPI server
    console.print("[cyan]Starting Yonca AI API server...[/cyan]\n")
    
    import uvicorn
    uvicorn.run(
        "yonca.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()