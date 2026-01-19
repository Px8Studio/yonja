# 🖥️ Yonca AI — Demo UI (Chainlit)

Isolated Chainlit frontend for Yonca AI farming assistant.

## 🚀 Quick Setup

### First Time Setup

```powershell
# From project root
cd demo-ui
.\setup.ps1
```

This creates a dedicated virtual environment in `demo-ui/.venv/` with Chainlit and dependencies.

### Running the UI

**Option 1: From VS Code**
- Run task: `🌿 Yonca AI: 🖥️ UI Start`

**Option 2: From Terminal**
```powershell
cd demo-ui
.\.venv\Scripts\Activate.ps1
chainlit run app.py -w --port 8501
```

## 🏗️ Architecture

```
yonja/                      ← Root: FastAPI backend
├── .venv/                  ← Poetry venv (backend deps)
├── pyproject.toml          ← Backend dependencies
└── demo-ui/                ← Frontend: Chainlit UI
    ├── .venv/              ← Separate venv (Chainlit deps)
    ├── requirements.txt    ← Frontend dependencies
    ├── app.py              ← Main Chainlit app
    └── .chainlit/          ← Chainlit config files
```

## 🔑 Key Points

- **Separate virtual environment** prevents dependency conflicts
- **Running Chainlit from root** creates files in wrong location
- **Always run from `demo-ui/`** to keep `.chainlit/` and `.files/` in the right place
- **VS Code tasks** automatically use `demo-ui/.venv/Scripts/chainlit.exe`

## 📚 Related Docs

- [CHAINLIT-NATIVE-ARCHITECTURE.md](docs/CHAINLIT-NATIVE-ARCHITECTURE.md)
- [Main Project README](../README.md)
