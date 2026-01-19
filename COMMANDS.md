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
