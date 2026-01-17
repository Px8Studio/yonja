# 🌿 Yonca AI - Farm Planning Assistant

> **AI-powered daily farm recommendations for Azerbaijani farmers.**  
> 100% offline-capable. 100% synthetic data. 100% rule-validated.

## 🎯 What This Is

**Yonca AI** is a **Headless AI Sidecar** that generates personalized farming task lists by combining:
- **Local LLM** (Qwen3-4B via Ollama) for natural language in Azerbaijani
- **Deterministic Agronomy Rules** to ensure ≥90% logical accuracy
- **Synthetic Farm Scenarios** so no real farmer data is ever needed

It plugs into Digital Umbrella's Yonca platform without touching their existing EKTIS/subsidy systems.

## ✨ Core Features

| Feature | Purpose |
|---------|---------|
| **Rules Registry** | 20+ agronomy rules with AZ- prefixes (irrigation, fertilization, pest control) |
| **Intent Matcher** | Understands Azerbaijani farming questions |
| **Schedule Service** | Generates daily task lists with priorities |
| **Lite Inference** | 3 modes: `standard` (Ollama), `lite` (GGUF), `offline` (rules-only) |
| **PII Gateway** | Strips personal data before AI processing |
| **Trust Scores** | Every recommendation cites its source rule |

## 🏗️ Architecture

```
yonca-ai/
├── src/yonca/
│   ├── sidecar/          # 🎯 CORE: Headless Intelligence Engine
│   │   ├── rules_registry    # Single truth: agronomy rules
│   │   ├── intent_matcher    # Azerbaijani NLU
│   │   ├── schedule_service  # Daily task generation
│   │   ├── recommendation_service  # Main orchestrator
│   │   ├── lite_inference    # Edge/offline modes
│   │   ├── pii_gateway       # Data sanitization
│   │   └── trust             # Confidence scoring
│   ├── api/              # REST & GraphQL endpoints
│   ├── data/             # Synthetic scenarios (7 farm types)
│   ├── models/           # Pydantic data models
│   └── umbrella/         # Streamlit demo UI
├── tests/                # Test suite
└── docs/                 # Documentation
```

**Key Principle:** The `sidecar/` is the intelligence engine. Everything else (API, UI) consumes it.

## 🚀 Quick Start

### Prerequisites

#### Option A: Local LLM with Ollama (Recommended for Azerbaijani 🇦🇿)

**Ollama is required for running local AI models.** This gives you:
- ✅ 100% offline capability
- ✅ No API costs
- ✅ Data never leaves your machine
- ✅ Best Azerbaijani language support with Qwen3

**Install Ollama:**

```bash
# Windows (via winget)
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

> ⚠️ **After installing Ollama, restart your terminal** for the PATH to update.

The Yonca startup manager will **automatically download the model** if it's not present!

#### Option B: Google Gemini (Cloud)

Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey) and set it in `.env`:

```bash
GOOGLE_API_KEY=your-api-key-here
YONCA_LLM_PROVIDER=gemini
YONCA_LLM_MODEL=gemini-2.0-flash
```

### Installation

> **Tooling Note:** We use **Poetry** for dependency management (reads `pyproject.toml`, creates reproducible environments). **Uvicorn** is the ASGI server that runs FastAPI—it's installed as a dependency, not a separate tool.

```bash
# Clone the repository
git clone https://github.com/ZekaLab/yonja.git
cd yonja

# Option A: Poetry (Recommended)
poetry install              # Creates .venv and installs all deps
poetry shell                # Activates the environment

# Option B: pip + venv
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -e ".[dev]"     # Install in editable mode
```

### 🎮 Start Yonca AI

**Option 1: VS Code (Recommended)**

Press `Ctrl+Shift+B` or run the task:
- **🌿 Start Yonca AI** - Full startup with Ollama health checks

**Option 2: Command Line**

```bash
# Automatic startup with health checks
python -m yonca.startup

# Or use the CLI command (after pip install -e .)
yonca
```

**Option 3: Check Status Only**

```bash
python -m yonca.startup --check-only
```

### What the Startup Manager Does

```
🌿 YONCA AI - Smart Farm Planning Assistant
═══════════════════════════════════════════

✅ Ollama installed
✅ Ollama server running
✅ Model qwen3:4b ready

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     🌿 Yonca AI Status             ┃
┣━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Component  ┃ Status                ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Ollama     │ ✅ Running            │
│ LLM Model  │ ✅ qwen3:4b           │
│ API        │ 🚀 Starting...        │
└────────────┴───────────────────────┘

Starting Yonca AI API server...
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Access the API

- **REST API Docs**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql

## 🤖 LLM Configuration

| Provider | Model | Size | Best For |
|----------|-------|------|----------|
| **Ollama** | `qwen3:4b` | 2.6GB | 🇦🇿 Azerbaijani (Recommended) |
| **Ollama** | `qwen3:1.7b` | 1.2GB | Fast responses, limited RAM |
| **Gemini** | `gemini-2.0-flash` | Cloud | Production, high volume |
| **Gemini** | `gemini-1.5-pro` | Cloud | Complex reasoning |

### Usage Example

```python
from yonca.agent import create_ollama_agent, create_gemini_agent

# Local Ollama (Azerbaijani-optimized)
agent = create_ollama_agent(model="qwen3:4b")
response = agent.chat("Buğda sahəsini nə vaxt suvarmaq lazımdır?")

# Google Gemini (Cloud)
agent = create_gemini_agent(api_key="your-key", model="gemini-2.0-flash")
response = agent.chat("Torpağın pH səviyyəsi nə olmalıdır?")
```

## 📡 API Endpoints

### REST API (`/api/v1/`)
```
GET  /farms                 → List 7 synthetic farm scenarios
GET  /farms/{id}            → Get specific farm profile
POST /recommendations       → Get AI recommendations
GET  /farms/{id}/schedule   → Get daily task schedule
POST /chatbot/message       → Chat in Azerbaijani
GET  /alerts/today          → Get weather/disease alerts
```

### Sidecar API (`/api/v1/sidecar/`)
```
POST /recommendations       → Full pipeline with PII gateway
GET  /status                → Service health + inference mode
POST /mode/{mode}           → Switch: standard/lite/offline
GET  /rulebook              → View agronomy rules (AZ- prefixes)
```

---

## 📊 Success Metrics

| Metric | Target | How We Achieve It |
|--------|--------|-------------------|
| **Logical Accuracy** | ≥90% | Rules Registry validates every LLM output |
| **Data Safety** | 100% | PII Gateway + Synthetic data only |
| **Offline Capability** | Yes | `offline` mode uses rules-only, no network |
| **Azerbaijani Support** | Native | Intent Matcher with Turkic dialect handling |
| **Integration Ready** | Yes | Same API contract as Yonca platform |

---

## 🧪 Testing

```bash
pytest tests/ -v --tb=short
```

## 📄 License

MIT License - ZekaLab © 2026
