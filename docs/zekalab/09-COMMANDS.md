# 🚀 Quick Command Reference

## 🎯 Three Ways to Run Commands

### Option 1: Poetry Shell (Recommended for Interactive Work)
```powershell
# Activate once per terminal session
poetry shell

# Then use commands directly
uvicorn yonca.api.main:app --reload
alembic upgrade head
chainlit run demo-ui/app.py --port 8501
pytest tests/
```

**Pros:** Clean, familiar command names
**Cons:** Need to activate in each new terminal

---

### Option 2: Poetry Run (No Activation Needed)
```powershell
# Run without activating - Poetry handles it
poetry run dev        # Start FastAPI server
poetry run migrate    # Run database migrations
poetry run seed       # Seed database
poetry run pytest     # Run tests
```

**Pros:** Works in any terminal, no activation
**Cons:** Extra `poetry run` prefix each time

---

### Option 3: Quick Activate Script
```powershell
# Auto-activates and shows available commands
.\activate.ps1

# Then use commands normally
uvicorn yonca.api.main:app --reload
alembic upgrade head
```

**Pros:** One-command activation with guidance
**Cons:** Requires script execution permissions

---

## 📋 Common Commands Quick Reference

| Task | Poetry Shell | Poetry Run | Direct Path |
|------|-------------|-----------|-------------|
| **Start API** | `uvicorn yonca.api.main:app --reload` | `poetry run dev` | `.\.venv\Scripts\python.exe -m uvicorn yonca.api.main:app --reload` |
| **Run Migrations** | `alembic upgrade head` | `poetry run migrate` | `.\.venv\Scripts\alembic.exe upgrade head` |
| **Seed Database** | `python scripts/seed_database.py` | `poetry run seed` | `.\.venv\Scripts\python.exe scripts/seed_database.py` |
| **Run Tests** | `pytest tests/` | `poetry run pytest tests/` | `.\.venv\Scripts\pytest.exe tests/` |
| **Run Linter** | `ruff check src/` | `poetry run ruff check src/` | `.\.venv\Scripts\ruff.exe check src/` |
| **Start Chainlit UI** | `chainlit run demo-ui/app.py` | - | `.\.venv\Scripts\chainlit.exe run demo-ui/app.py` |

---

## 🌍 Environment Configuration (Two-Axis Model)

Yonca uses a **two-axis deployment model** for clarity:

| Axis | Variable | Values | Purpose |
|------|----------|--------|---------|
| **Environment** | `YONCA_ENVIRONMENT` | `development`, `staging`, `production` | WHAT stage of development |
| **Infrastructure** | `YONCA_INFRASTRUCTURE_MODE` | `local`, `cloud` | WHERE it runs |

### Configuration Matrix

| Scenario | Environment | Infrastructure | LLM Provider | Checkpointer |
|----------|-------------|----------------|--------------|--------------|
| **Local Dev** | development | local | ollama | memory/redis |
| **Local Staging** | staging | local | groq | postgres |
| **Cloud Staging** | staging | cloud | gemini | postgres |
| **Production** | production | cloud | groq/vllm | postgres |

### Example .env Configurations

**Local Development:**
```bash
YONCA_ENVIRONMENT=development
YONCA_INFRASTRUCTURE_MODE=local
YONCA_LLM_PROVIDER=ollama
YONCA_LANGGRAPH_REQUIRED=true
```

**Cloud Production:**
```bash
YONCA_ENVIRONMENT=production
YONCA_INFRASTRUCTURE_MODE=cloud
YONCA_LLM_PROVIDER=groq
YONCA_LANGGRAPH_REQUIRED=true
```

---

## ⚠️ Troubleshooting

### "Command not recognized" Error
```powershell
# Problem:
PS> uvicorn yonca.api.main:app --reload
uvicorn: The term 'uvicorn' is not recognized...

# Solution 1: Activate Poetry shell
poetry shell
uvicorn yonca.api.main:app --reload

# Solution 2: Use Poetry run
poetry run dev

# Solution 3: Use quick activate
.\activate.ps1
uvicorn yonca.api.main:app --reload
```

### First Time Setup
```powershell
# Install dependencies
poetry install

# Verify installation
poetry run python --version
poetry run uvicorn --version
poetry run alembic --version

# Start development
poetry shell
```

---

## 🐳 Docker Multi-Environment Deployment

Yonca now uses a modular Docker Compose structure for different deployment stages.

### 1. Development (Local)
Full stack with local Ollama, LangGraph server, API, and UI.
```powershell
# Start base infrastructure (DBs, Redis, Langfuse)
docker compose -f docker-compose.base.yml up -d

# Start application services (API, UI, LangGraph)
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up -d

# One-time model setup (if needed)
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml run --rm model-setup
```

### 2. Staging (Cloud-Parity)
Uses Groq for cloud-scale LLM testing.
```powershell
# Requires GROQ_API_KEY in .env
docker compose -f docker-compose.base.yml -f docker-compose.staging.yml up -d
```

---

## 🎨 LangGraph Studio

LangGraph Studio provides a visual interface for debugging your agent's state machine.

### Accessing Studio
1. **Open LangGraph Studio** (Desktop App)
2. **Select Project**: Point it to the `yonja` root directory.
3. **Connectivity**: Ensure the Dev Server is running (`localhost:2024`).
4. **Visual Debugging**: View node execution, message history, and manually trigger tool calls.

---

## 🎓 Understanding the Environment

**Poetry** creates an isolated environment in `.venv/` with all dependencies.

**Three ways to use it:**
1. **Activate it** (`poetry shell`) → commands work directly
2. **Prefix commands** (`poetry run <cmd>`) → no activation needed
3. **Use full paths** (`.\.venv\Scripts\<cmd>`) → works but verbose

**Recommended workflow:**
- **Interactive development:** Use `poetry shell` once per session
- **CI/CD & scripts:** Use `poetry run` for reproducibility
- **Quick tasks:** Use VS Code tasks (they handle paths automatically)

---

## 💡 Pro Tips

1. **Add to your PowerShell profile** (auto-activate on `cd`):
   ```powershell
   # Edit: $PROFILE
   function yonca {
       cd C:\Users\rjjaf\_Projects\yonja
       poetry shell
   }
   ```

2. **Use VS Code integrated terminal** - It respects the virtual environment

3. **Use VS Code tasks** (Ctrl+Shift+P → "Run Task") - Pre-configured with correct paths

4. **Check if environment is active:**
   ```powershell
   # Look for (yonca-ai) prefix in prompt
   (yonca-ai) PS C:\Users\rjjaf\_Projects\yonja>
   ```

---

For more details, see:
- [README.md](README.md) - Full project documentation
- [QUICK-START.md](QUICK-START.md) - Testing guide
- [.vscode/tasks.json](.vscode/tasks.json) - Pre-configured VS Code tasks
