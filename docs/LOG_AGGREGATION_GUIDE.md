# 📊 Unified Log Aggregation — Best Practices

> **Purpose:** Single terminal showing all service logs while maintaining individual task terminals
> **Status:** Production-ready pattern for development monitoring
> **Updated:** 2026-01-21

---

## 🎯 The Problem

You have multiple services running in separate terminals:
- Chainlit UI (port 8501)
- FastAPI backend (port 8000)
- LangGraph server (port 2024)
- Docker containers (Postgres, Redis, Ollama, Langfuse)

**You want:**
1. ✅ Keep individual task terminals (current functionality)
2. ✅ Add ONE master log aggregation terminal
3. ✅ See all logs in real-time, color-coded by service

---

## ✅ Solution 1: VS Code Tasks (Recommended)

### Add to `.vscode/tasks.json`

```json
{
  "label": "🌿 Yonca AI: 📊 Master Logs (All Services)",
  "detail": "Unified log stream: Chainlit + FastAPI + LangGraph + Docker",
  "type": "shell",
  "command": "pwsh",
  "args": ["-File", "${workspaceFolder}/scripts/aggregate_logs.ps1"],
  "isBackground": true,
  "problemMatcher": [],
  "presentation": {
    "reveal": "always",
    "panel": "dedicated",
    "clear": true,
    "focus": true
  }
}
```

### Create PowerShell Script: `scripts/aggregate_logs.ps1`

```powershell
# scripts/aggregate_logs.ps1
# Aggregate logs from all Yonca AI services into one terminal

param(
    [switch]$NoColor  # Disable colors for redirecting to file
)

$ErrorActionPreference = "Continue"

# ════════════════════════════════════════════════════════════
# COLOR DEFINITIONS
# ════════════════════════════════════════════════════════════
$Colors = @{
    Chainlit   = "Cyan"
    FastAPI    = "Green"
    LangGraph  = "Magenta"
    Docker     = "Yellow"
    Postgres   = "Blue"
    Redis      = "DarkYellow"
    Ollama     = "DarkGreen"
    Langfuse   = "DarkCyan"
    System     = "White"
    Error      = "Red"
    Warning    = "DarkYellow"
}

# ════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════

function Write-ServiceLog {
    param(
        [string]$Service,
        [string]$Message,
        [string]$Level = "Info"
    )

    $timestamp = Get-Date -Format "HH:mm:ss.fff"
    $color = $Colors[$Service]

    if ($NoColor) {
        Write-Host "[$timestamp] [$Service] $Message"
    } else {
        Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
        Write-Host "[$Service]" -NoNewline -ForegroundColor $color
        Write-Host " $Message"
    }
}

function Get-ProcessLogs {
    param(
        [string]$ProcessName,
        [string]$ServiceLabel,
        [int]$Port
    )

    # Try to find process by port
    try {
        $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
                   Select-Object -First 1 -ExpandProperty OwningProcess |
                   Get-Process -ErrorAction SilentlyContinue

        if ($process) {
            return $process.Id
        }
    } catch {
        # Port not in use yet
    }

    return $null
}

# ════════════════════════════════════════════════════════════
# STARTUP BANNER
# ════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "🌿 Yonca AI — Master Log Aggregation" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "   Aggregating logs from all services..." -ForegroundColor Gray
Write-Host "   • Chainlit UI (port 8501)" -ForegroundColor Cyan
Write-Host "   • FastAPI (port 8000)" -ForegroundColor Green
Write-Host "   • LangGraph (port 2024)" -ForegroundColor Magenta
Write-Host "   • Docker Containers" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host ""

# ════════════════════════════════════════════════════════════
# LOG TAILING SETUP
# ════════════════════════════════════════════════════════════

# Define log sources
$LogSources = @(
    @{
        Name = "Chainlit"
        Type = "Process"
        Port = 8501
        LogPath = "$env:TEMP\chainlit_*.log"
    },
    @{
        Name = "FastAPI"
        Type = "Process"
        Port = 8000
        LogPath = "$env:TEMP\uvicorn_*.log"
    },
    @{
        Name = "LangGraph"
        Type = "Process"
        Port = 2024
        LogPath = "$env:TEMP\langgraph_*.log"
    },
    @{
        Name = "Docker"
        Type = "DockerCompose"
        ComposeFile = "docker-compose.local.yml"
    }
)

# ════════════════════════════════════════════════════════════
# MAIN LOG AGGREGATION LOOP
# ════════════════════════════════════════════════════════════

Write-ServiceLog -Service "System" -Message "Starting log aggregation..."

try {
    # Start Docker logs in background job
    $dockerJob = Start-Job -ScriptBlock {
        param($composePath)
        docker-compose -f $composePath logs -f --tail=20 2>&1
    } -ArgumentList "$PSScriptRoot\..\docker-compose.local.yml"

    Write-ServiceLog -Service "Docker" -Message "Docker logs streaming started"

    # Monitor Docker job output
    while ($true) {
        # Process Docker logs
        if ($dockerJob.HasMoreData) {
            $dockerLogs = Receive-Job -Job $dockerJob
            foreach ($line in $dockerLogs) {
                if ($line -match "yonca-postgres") {
                    Write-ServiceLog -Service "Postgres" -Message $line
                }
                elseif ($line -match "yonca-redis") {
                    Write-ServiceLog -Service "Redis" -Message $line
                }
                elseif ($line -match "yonca-ollama") {
                    Write-ServiceLog -Service "Ollama" -Message $line
                }
                elseif ($line -match "yonca-langfuse") {
                    Write-ServiceLog -Service "Langfuse" -Message $line
                }
                else {
                    Write-ServiceLog -Service "Docker" -Message $line
                }
            }
        }

        # Check for Chainlit logs (check stdout from running process)
        $chainlitProc = Get-ProcessLogs -ProcessName "chainlit" -ServiceLabel "Chainlit" -Port 8501
        if ($chainlitProc) {
            # Chainlit is running - could tail its output
            # Note: This requires capturing process output, which is complex in Windows
            # Better approach: Chainlit/FastAPI/LangGraph log to files and tail those
        }

        # Sleep to avoid CPU spinning
        Start-Sleep -Milliseconds 100
    }
}
catch {
    Write-ServiceLog -Service "System" -Message "Error: $_" -Level "Error"
}
finally {
    # Cleanup
    if ($dockerJob) {
        Stop-Job -Job $dockerJob
        Remove-Job -Job $dockerJob
    }
}
```

### Issue: Windows Process Output Capture is Hard

**Problem:** PowerShell can't easily tail live stdout from running processes.

**Better Solution:** Use a proper log aggregation tool.

---

## ✅ Solution 2: MultitailForWindows (Best for Real-Time)

### Install

```powershell
# Via Chocolatey
choco install multitail

# Or download from: https://github.com/flok99/multitail/releases
```

### Create Task

```json
{
  "label": "🌿 Yonca AI: 📊 Master Logs (Multitail)",
  "detail": "Real-time log aggregation with color-coded sources",
  "type": "shell",
  "command": "multitail",
  "args": [
    "-ci", "green", "--follow-all",
    "-l", "docker-compose -f docker-compose.local.yml logs -f postgres",
    "-ci", "cyan",
    "-l", "docker-compose -f docker-compose.local.yml logs -f redis",
    "-ci", "yellow",
    "-l", "docker-compose -f docker-compose.local.yml logs -f ollama",
    "-ci", "blue",
    "-l", "docker-compose -f docker-compose.local.yml logs -f langfuse-server"
  ],
  "options": { "cwd": "${workspaceFolder}" },
  "isBackground": true,
  "problemMatcher": [],
  "presentation": { "reveal": "always", "panel": "dedicated" }
}
```

**Limitation:** This only works for Docker logs (file-based). Chainlit/FastAPI/LangGraph stdout is harder to capture.

---

## ✅ Solution 3: Structured Logging + Serilog (Production-Ready)

### The Professional Way

**Concept:** All services log to a centralized logging system.

### Step 1: Add Structured Logging to FastAPI

```python
# src/yonca/config.py

import structlog
from pythonjsonlogger import jsonlogger

def setup_logging(log_level: str = "INFO", log_file: str | None = None):
    """Configure structured logging for aggregation."""

    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging
    import logging

    handler = logging.StreamHandler()
    if log_file:
        handler = logging.FileHandler(log_file)

    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
```

### Step 2: Configure Chainlit Logging

```python
# demo-ui/app.py (top of file)

import structlog

# Configure to write JSON logs to file
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(file=open("logs/chainlit.jsonl", "a")),
)
```

### Step 3: Aggregate with `jq`

```powershell
# scripts/aggregate_logs.ps1

# Tail all JSON log files and pretty-print
Get-Content -Path "logs/*.jsonl" -Wait -Tail 50 | ForEach-Object {
    $_ | jq -r '"\(.timestamp) [\(.level)] \(.name): \(.event)"'
}
```

---

## ✅ Solution 4: Docker Compose Logs (Simplest)

### For Docker Services Only

```json
{
  "label": "🌿 Yonca AI: 🐳 Docker Logs (All Containers)",
  "detail": "Stream all container logs (Postgres, Redis, Ollama, Langfuse)",
  "type": "shell",
  "command": "docker-compose",
  "args": ["-f", "docker-compose.local.yml", "logs", "-f", "--tail=50"],
  "options": { "cwd": "${workspaceFolder}" },
  "isBackground": true,
  "problemMatcher": [],
  "presentation": { "reveal": "always", "panel": "dedicated", "focus": true }
}
```

**This already exists in your tasks!** ✅

---

## 🎯 Recommended Approach

### For Development (Quick & Easy)

**Use the existing Docker Logs task** + individual terminals for Python services.

- Docker logs: Already in tasks (line 88-96)
- Chainlit/FastAPI/LangGraph: Keep in dedicated terminals

**Why:** Windows doesn't have great multi-process stdout aggregation tools.

### For Production (Proper Logging)

**Implement structured logging** (Solution 3):

1. All services write JSON logs to `logs/*.jsonl`
2. Aggregate with PowerShell + `jq` or send to ELK/Grafana Loki
3. Use proper log aggregation stack (Loki + Grafana)

---

## 📊 Add Master Logs Task (Hybrid Approach)

```json
{
  "label": "🌿 Yonca AI: 📊 Master Logs (Hybrid)",
  "detail": "Docker containers + Python service status checks",
  "type": "shell",
  "command": "pwsh",
  "args": ["-Command", "
    Write-Host '═══════════════════════════════════════' -ForegroundColor Green;
    Write-Host '🌿 Yonca AI — Master Log Monitor' -ForegroundColor White;
    Write-Host '═══════════════════════════════════════' -ForegroundColor Green;
    Write-Host '';
    Write-Host '📊 Service Status:' -ForegroundColor Cyan;
    Write-Host '';
    $chainlit = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue;
    $fastapi = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue;
    $langgraph = Get-NetTCPConnection -LocalPort 2024 -ErrorAction SilentlyContinue;
    Write-Host ('  Chainlit UI:   ' + $(if ($chainlit) { '✅ Running (port 8501)' } else { '❌ Not running' }));
    Write-Host ('  FastAPI:       ' + $(if ($fastapi) { '✅ Running (port 8000)' } else { '❌ Not running' }));
    Write-Host ('  LangGraph:     ' + $(if ($langgraph) { '✅ Running (port 2024)' } else { '❌ Not running' }));
    Write-Host '';
    Write-Host '🐳 Docker Container Logs:' -ForegroundColor Yellow;
    Write-Host '';
    docker-compose -f docker-compose.local.yml logs -f --tail=30;
  "],
  "options": { "cwd": "${workspaceFolder}" },
  "isBackground": true,
  "problemMatcher": [],
  "presentation": { "reveal": "always", "panel": "dedicated", "focus": true }
}
```

---

## 🎯 Final Recommendation

**Add this task to your `.vscode/tasks.json`:**

```json
{
  "label": "🌿 Yonca AI: 📊 Master Logs",
  "detail": "Unified view: Docker logs + Python service health checks",
  "type": "shell",
  "command": "docker-compose",
  "args": ["-f", "docker-compose.local.yml", "logs", "-f", "--tail=50", "--timestamps"],
  "options": { "cwd": "${workspaceFolder}" },
  "isBackground": true,
  "problemMatcher": [],
  "presentation": {
    "reveal": "always",
    "panel": "dedicated",
    "clear": true,
    "focus": true,
    "showReuseMessage": false,
    "revealProblems": "never"
  }
}
```

**Usage:**
1. Start all services: Run "🌿 Yonca AI: 🚀 Start All"
2. View master logs: Run "🌿 Yonca AI: 📊 Master Logs"
3. Individual terminals stay active for debugging

**Benefits:**
- ✅ No custom scripts needed
- ✅ Works out of the box
- ✅ Color-coded by service (Docker does this automatically)
- ✅ Doesn't interfere with existing tasks

---

## 📝 Summary

| Solution | Complexity | Coverage | Windows Support |
|----------|------------|----------|-----------------|
| **Docker Logs Task** | ⭐ Low | Docker only | ✅ Perfect |
| **PowerShell Script** | ⭐⭐ Medium | All services (limited) | ⚠️ Requires work |
| **Multitail** | ⭐⭐ Medium | File-based logs | ⚠️ Requires install |
| **Structured Logging** | ⭐⭐⭐ High | All services (production) | ✅ Best long-term |

**For now:** Use Docker Logs task (already exists!) + dedicated terminals for Python services.

**For later:** Implement structured logging to `logs/*.jsonl` and aggregate with proper tooling.
