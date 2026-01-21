# LangGraph Dev Server Startup Guide

## Overview

This guide covers how to start the **LangGraph Dev Server** in various scenarios, including proper environment configuration to avoid `ModuleNotFoundError`.

## Quick Start

### Option 1: VS Code Tasks (Recommended)

```
Ctrl+Shift+P → "Run Task" → "🌿 Yonca AI: 🚀 Start All"
```

This automatically starts all services in the correct order:
1. Quality checks
2. Docker services
3. FastAPI
4. Chainlit UI
5. **LangGraph Dev Server**

### Option 2: Manual Start

```powershell
# Set environment
$env:PYTHONPATH = "c:\Users\rjjaf\_Projects\yonja\src"

# Start dev server
.\.venv\Scripts\langgraph.exe dev
```

### Option 3: CLI Script

```powershell
.\scripts\start_all.ps1
```

## Environment Configuration

### Required Environment Variables

The LangGraph Dev Server **must** have `PYTHONPATH` set correctly:

```powershell
# Windows PowerShell
$env:PYTHONPATH = "${workspaceFolder}\src"

# Windows CMD
set PYTHONPATH=%workspaceFolder%\src

# Linux/macOS
export PYTHONPATH=/path/to/project/src
```

### Why PYTHONPATH Matters

LangGraph Dev Server loads your graph module:
```json
// langgraph.json
{
  "graphs": {
    "yonca_agent": "./src/yonca/agent/graph.py:create_agent_graph"
  }
}
```

Without `PYTHONPATH`, imports like `from yonca.agent.state import State` will fail with:
```
ModuleNotFoundError: No module named 'yonca'
```

### Configuration Files

#### 1. langgraph.json
**Location**: Project root
**Purpose**: Graph registry

```json
{
  "$schema": "https://langchain-ai.github.io/langgraph/langgraph.json",
  "dependencies": ["."],
  "graphs": {
    "yonca_agent": "./src/yonca/agent/graph.py:create_agent_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

#### 2. .env
**Location**: Project root
**Purpose**: Environment variables

```bash
# LangGraph Dev Server
LANGGRAPH_DEV_HOST=localhost
LANGGRAPH_DEV_PORT=2024
LANGGRAPH_BASE_URL=http://localhost:2024
LANGGRAPH_API_LOG_LEVEL=DEBUG

# LangSmith Tracing (optional)
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=yonca-demo
LANGSMITH_API_KEY=your-api-key
```

## VS Code Task Configuration

### LangGraph Start Task

**File**: `.vscode/tasks.json`

```json
{
  "label": "🌿 Yonca AI: 🎨 LangGraph Start",
  "detail": "Running 🤖 LangGraph Agent + orchestration (http://localhost:2024)",
  "type": "shell",
  "command": "${workspaceFolder}\\.venv\\Scripts\\langgraph.exe",
  "args": ["dev"],
  "options": {
    "cwd": "${workspaceFolder}",
    "env": {
      "PYTHONPATH": "${workspaceFolder}/src"
    }
  },
  "isBackground": true,
  "problemMatcher": {
    "owner": "langgraph",
    "pattern": { "regexp": "^$" },
    "background": {
      "activeOnStart": true,
      "beginsPattern": "Starting",
      "endsPattern": "Ready"
    }
  },
  "presentation": {
    "reveal": "always",
    "panel": "dedicated",
    "clear": true
  }
}
```

### Key Points

1. **Command**: Uses virtual environment's `langgraph.exe`
2. **Args**: `["dev"]` starts the dev server
3. **CWD**: Project root (where `langgraph.json` lives)
4. **PYTHONPATH**: Set to `${workspaceFolder}/src`
5. **Background**: Runs as background task (non-blocking)

## PowerShell Startup Script

**File**: `scripts/start_all.ps1`

```powershell
# Set PYTHONPATH for LangGraph
$env:PYTHONPATH = "$projectRoot\src"

# Start LangGraph Dev Server
Write-Host "🎨 Starting LangGraph Dev Server..." -ForegroundColor Yellow
Start-Process -FilePath "$venvPath\langgraph.exe" `
              -ArgumentList "dev" `
              -WorkingDirectory $projectRoot `
              -WindowStyle Hidden
```

## Verification

### Check if Running

```powershell
# Check process
Get-Process -Name langgraph -ErrorAction SilentlyContinue

# Check HTTP endpoint
curl http://localhost:2024/health

# Check logs in VS Code terminal panel
```

### Expected Output

```
Starting LangGraph dev server...
Loading graph: yonca_agent
Graph loaded successfully
Server running at http://localhost:2024
Ready to accept requests
```

## Common Issues

### 1. ModuleNotFoundError: No module named 'yonca'

**Symptom**:
```
ModuleNotFoundError: No module named 'yonca'
```

**Solution**:
```powershell
# Set PYTHONPATH before starting
$env:PYTHONPATH = "c:\Users\rjjaf\_Projects\yonja\src"
.\.venv\Scripts\langgraph.exe dev
```

### 2. Port Already in Use

**Symptom**:
```
Error: Address already in use: 2024
```

**Solution**:
```powershell
# Kill existing process
Get-Process -Name langgraph -ErrorAction SilentlyContinue | Stop-Process -Force

# Restart
.\.venv\Scripts\langgraph.exe dev
```

### 3. Graph Not Found

**Symptom**:
```
Error: Graph 'yonca_agent' not found
```

**Solution**:
Check `langgraph.json`:
```json
{
  "graphs": {
    "yonca_agent": "./src/yonca/agent/graph.py:create_agent_graph"
  }
}
```

Ensure path is correct and function exists.

### 4. Import Errors in Graph Module

**Symptom**:
```
ImportError: cannot import name 'State' from 'yonca.agent.state'
```

**Solution**:
1. Verify `PYTHONPATH` is set
2. Check virtual environment is activated
3. Verify all dependencies are installed:
   ```powershell
   .\.venv\Scripts\pip install -e .
   ```

## Development Workflow

### 1. Code Changes

When modifying graph code, the dev server auto-reloads:

```python
# src/yonca/agent/graph.py
def create_agent_graph() -> CompiledGraph:
    # Make changes here
    pass
```

Dev server detects changes and reloads automatically.

### 2. Testing API Mode

Start Chainlit in API mode to test HTTP integration:

```powershell
# Terminal 1: Start LangGraph Dev Server
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\langgraph.exe dev

# Terminal 2: Start Chainlit in API mode
$env:INTEGRATION_MODE = "api"
$env:YONCA_API_URL = "http://localhost:8000"
.\demo-ui\.venv\Scripts\chainlit.exe run app.py -w --port 8501
```

### 3. Debugging

Enable verbose logging:

```powershell
# Set environment variables
$env:LANGGRAPH_API_LOG_LEVEL = "DEBUG"
$env:LANGCHAIN_TRACING_V2 = "true"

# Start with debug output
.\.venv\Scripts\langgraph.exe dev
```

## Integration with Other Services

### Architecture Overview

```
┌─────────────────┐
│   Chainlit UI   │ (http://localhost:8501)
│  Integration    │
│  Mode: direct   │
└────────┬────────┘
         │
         │ Direct in-process
         ▼
┌─────────────────┐
│   LangGraph     │ (in-process)
│   Agent Graph   │
└─────────────────┘

        OR

┌─────────────────┐
│   Chainlit UI   │ (http://localhost:8501)
│  Integration    │
│  Mode: api      │
└────────┬────────┘
         │
         │ HTTP POST
         ▼
┌─────────────────┐
│   FastAPI       │ (http://localhost:8000)
│   Graph Routes  │
└────────┬────────┘
         │
         │ HTTP POST
         ▼
┌─────────────────┐
│   LangGraph     │ (http://localhost:2024)
│   Dev Server    │
└─────────────────┘
```

### Service Dependencies

1. **Docker Services** (must start first):
   - PostgreSQL (port 5433)
   - Redis (port 6379)
   - Ollama (port 11434)
   - Langfuse (port 3001)

2. **LangGraph Dev Server** (independent):
   - No hard dependencies
   - Can start in any order
   - Only needed for API mode testing

3. **FastAPI** (depends on Docker):
   - Requires PostgreSQL
   - Requires Redis
   - Can run without LangGraph Dev Server

4. **Chainlit UI** (depends on mode):
   - **Direct mode**: No LangGraph Dev Server needed
   - **API mode**: Requires FastAPI + LangGraph Dev Server

## Production Deployment

### Docker Compose Service (Coming Next)

We'll add a `yonca-langgraph` service to `docker-compose.local.yml`:

```yaml
services:
  yonca-langgraph:
    build:
      context: .
      dockerfile: Dockerfile.langgraph
    ports:
      - "2024:2024"
    environment:
      - PYTHONPATH=/app/src
      - LANGGRAPH_API_LOG_LEVEL=INFO
    volumes:
      - ./src:/app/src
    depends_on:
      - postgres
      - redis
```

### Kubernetes/Cloud Deployment

For production, LangGraph Dev Server runs as a separate service:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yonca-langgraph
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: langgraph-dev
        image: yonca-langgraph:latest
        ports:
        - containerPort: 2024
        env:
        - name: PYTHONPATH
          value: /app/src
        - name: LANGGRAPH_API_LOG_LEVEL
          value: INFO
```

## Monitoring

### Health Check

```bash
# Simple health check
curl http://localhost:2024/health

# Expected response
{"status": "ok", "version": "0.1.0"}
```

### Logs

View logs in VS Code terminal or via:

```powershell
# VS Code: Panel shows "🎨 LangGraph Start"

# CLI: No direct log file (stdout only)
```

### LangSmith Tracing

If enabled, view traces at https://smith.langchain.com/:

```bash
# Enable in .env
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=yonca-demo
LANGSMITH_API_KEY=your-key
```

## Summary

✅ **PYTHONPATH** is the critical environment variable
✅ **VS Code tasks** handle this automatically
✅ **Manual starts** require explicit `$env:PYTHONPATH` setup
✅ **No changes** needed to existing scripts (already correct)

## Next Steps

1. ✅ Environment setup documented
2. ⏳ Add Dockerfile for containerized deployment
3. ⏳ Add docker-compose service definition
4. ⏳ Add health checks and monitoring

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Dev Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)
- [VS Code Tasks](https://code.visualstudio.com/docs/editor/tasks)
