# 🏗️ Yonca AI — Proper Architecture Setup

## 🎯 Problem Summary

Running `poetry run chainlit` from the root folder creates Chainlit configuration files (`.chainlit/`, `.files/`) in the **wrong location** because:

1. Chainlit is a **frontend-only** dependency
2. It should live in `demo-ui/.venv/`, not root `.venv/`
3. Running from root pollutes the workspace with frontend files

## ✅ Solution: Separate Virtual Environments

### Architecture

```
yonja/                          # Root workspace
│
├── .venv/                      # Backend Python environment (Poetry)
│   └── Scripts/
│       ├── python.exe
│       ├── uvicorn.exe         # FastAPI server
│       ├── langgraph.exe       # Agent orchestration
│       ├── alembic.exe         # Database migrations
│       └── pytest.exe          # Testing
│
├── pyproject.toml              # Backend dependencies ONLY
├── poetry.lock
│
└── demo-ui/                    # Frontend application (Chainlit)
    ├── .venv/                  # Frontend Python environment (pip)
    │   └── Scripts/
    │       ├── python.exe
    │       └── chainlit.exe    # ← Chainlit lives HERE
    │
    ├── requirements.txt        # Frontend dependencies
    ├── app.py                  # Main Chainlit app
    └── .chainlit/              # ← Generated files stay HERE
        ├── config.toml
        └── oauth.json
```

## 🚀 Step-by-Step Setup

### 1️⃣ Clean Up (If Needed)

```powershell
# Remove Chainlit from root if installed
cd C:\Users\rjjaf\_Projects\yonja
poetry remove chainlit

# Clean up root Poetry environment
poetry lock
poetry install

# Remove any Chainlit files in root
Remove-Item -Recurse -Force .chainlit -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .files -ErrorAction SilentlyContinue
```

### 2️⃣ Setup Backend (Root)

```powershell
# Install backend dependencies with Poetry
cd C:\Users\rjjaf\_Projects\yonja
poetry install

# Verify backend tools
poetry run uvicorn --version
poetry run langgraph --version
poetry run alembic --version
```

### 3️⃣ Setup Frontend (demo-ui)

```powershell
# Navigate to frontend folder
cd C:\Users\rjjaf\_Projects\yonja\demo-ui

# Create isolated virtual environment
python -m venv .venv

# Activate and install Chainlit
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# Verify Chainlit installation
chainlit --version
```

### 4️⃣ Verify VS Code Tasks

The `.vscode/tasks.json` has been updated to use the correct path:

```json
{
    "label": "🌿 Yonca AI: 🖥️ UI Start",
    "command": "${workspaceFolder}\\demo-ui\\.venv\\Scripts\\chainlit.exe",
    "options": {
        "cwd": "${workspaceFolder}/demo-ui"
    }
}
```

## 🎮 Usage

### From VS Code

- **Start All**: Run task `🌿 Yonca AI: 🚀 Start All`
- **Start UI Only**: Run task `🌿 Yonca AI: 🖥️ UI Start`

### From Terminal

#### Backend (FastAPI + LangGraph)
```powershell
# Activate root environment
cd C:\Users\rjjaf\_Projects\yonja
poetry shell

# Run backend
uvicorn yonca.api.main:app --reload
```

#### Frontend (Chainlit)
```powershell
# Activate demo-ui environment
cd C:\Users\rjjaf\_Projects\yonja\demo-ui
.\.venv\Scripts\Activate.ps1

# Run Chainlit
chainlit run app.py -w --port 8501
```

## 📦 Dependency Management

### Adding Backend Dependencies

```powershell
cd C:\Users\rjjaf\_Projects\yonja
poetry add <package-name>
```

### Adding Frontend Dependencies

```powershell
cd C:\Users\rjjaf\_Projects\yonja\demo-ui
.\.venv\Scripts\Activate.ps1
pip install <package-name>
pip freeze > requirements.txt
```

## 🔍 Troubleshooting

### "chainlit.exe not found"

**Cause**: Chainlit not installed in `demo-ui/.venv/`

**Fix**:
```powershell
cd demo-ui
.\.venv\Scripts\Activate.ps1
pip install chainlit
```

### ".chainlit/ files appear in root"

**Cause**: Running `chainlit` from root folder or wrong environment

**Fix**:
```powershell
# Always run from demo-ui folder
cd demo-ui
.\.venv\Scripts\Activate.ps1
chainlit run app.py
```

### "Module not found" errors in Chainlit

**Cause**: Missing dependencies in `demo-ui/.venv/`

**Fix**:
```powershell
cd demo-ui
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## ✅ Benefits of This Architecture

1. **Clean Separation**: Backend and frontend don't pollute each other
2. **Independent Deployment**: Can containerize separately
3. **Faster Installs**: Only install what each part needs
4. **Easier Debugging**: Clear which environment has issues
5. **Better Git History**: `.gitignore` properly configured

## 📚 Related Files

- [pyproject.toml](../pyproject.toml) — Backend dependencies
- [demo-ui/requirements.txt](requirements.txt) — Frontend dependencies
- [.vscode/tasks.json](../.vscode/tasks.json) — Task configurations
- [.gitignore](../.gitignore) — Ignore `demo-ui/.venv/`
