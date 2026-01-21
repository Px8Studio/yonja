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

### Installation

> **🎯 Quick Tip:** Run `.\activate.ps1` or `activate.bat` for instant setup! See [COMMANDS.md](COMMANDS.md) for all usage options.

> **Tooling Note:** We use **Poetry** for dependency management (reads `pyproject.toml`, creates reproducible environments). **Uvicorn** is the ASGI server that runs FastAPI—it's installed as a dependency, not a separate tool.

```bash
# Clone the repository
git clone https://github.com/ZekaLab/yonja.git
cd yonja

# Option A: Poetry (Recommended)
poetry install              # Core dependencies
poetry shell                # Activates the environment

# Option B: Quick activate script
.\activate.ps1              # Windows PowerShell
activate.bat                # Windows CMD

# Option C: pip + venv
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -e ".[dev]"     # Install in editable mode
```

**💡 Can't run `uvicorn` or `alembic` directly?**
→ See [COMMANDS.md](COMMANDS.md) for three ways to run commands without path issues.

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

### Two Deployment Modes

**MODE 1: Groq Cloud (Benchmark)**
- Purpose: Proves what's possible with open-source models
- Performance: 200-300 tok/s (enterprise-grade)
- Cost: $0-50/mo (free tier available)
- Use for: Development, testing, proof-of-concept

**MODE 2: DigiRella Self-Hosted (Production)**
- Purpose: Same performance as Groq, your infrastructure
- Performance: 200-300 tok/s (matches Groq)
- Cost: $2,600-145k one-time OR $470-7,600/mo (rented GPU)
- Use for: Production, data sovereignty, air-gapped

📚 See [PRICING-SIMPLIFIED.md](docs/PRICING-SIMPLIFIED.md) for full comparison

### Available Models (All Open-Source)

| Provider | Model | Deployment | Performance |
|----------|-------|------------|-------------|
| **Groq** | `llama-4-maverick-17b` | Cloud | 🚀 300 tok/s (benchmark) |
| **Groq** | `llama-3.3-70b` | Cloud | 🚀 200+ tok/s |
| **Groq** | `qwen3-32b` | Cloud | 🚀 280 tok/s |
| **DigiRella** | Same models | Self-hosted | 🏠 200-300 tok/s |
| **Ollama** | `qwen3:4b` | Local | 🇦🇿 Offline-capable |
| **Ollama** | `atllama:7b` | Local | 🇦🇿 Azerbaijani-tuned |

> **Key:** Groq = Cloud benchmark | DigiRella = Self-hosted equivalent | Ollama = Lightweight local

### Setting Up Local Models (Ollama)

**Option 1: Docker (Recommended)**
```bash
# Start all services and setup models
docker-compose -f docker-compose.local.yml up -d

# First-time setup: pull qwen3 and import ATLLaMA
docker-compose -f docker-compose.local.yml --profile setup up model-setup
```

**Option 2: Manual Setup**
```powershell
# Pull Qwen3 (primary model)
ollama pull qwen3:4b

# Import ATLLaMA from GGUF (Azerbaijani-tuned)
python scripts/import_model.py --name atllama --path models/atllama.v3.5.Q4_K_M.gguf

# Or import into Docker container
python scripts/import_model.py --docker
```

### Switching Models

Set the model via environment variable:
```bash
YONCA_OLLAMA_MODEL=qwen3:4b   # Qwen3 (default)
YONCA_OLLAMA_MODEL=atllama    # ATLLaMA (Azerbaijani)
```

Or use the API:
```bash
# List available models
curl http://localhost:8000/api/models

# Check model status
curl http://localhost:8000/api/models/qwen3:4b
```

### Usage Example

```python
from yonca.agent import create_ollama_agent
from yonca.llm import create_groq_provider

# Local Ollama (Azerbaijani-optimized)
agent = create_ollama_agent(model="qwen3:4b")
response = agent.chat("Buğda sahəsini nə vaxt suvarmaq lazımdır?")

# Groq Cloud (Ultra-fast open-source models - benchmark)
llm = create_groq_provider(api_key="your-key", model="llama-4-maverick-17b-128e-instruct")
response = await llm.generate([
    LLMMessage.user("Torpağın pH səviyyəsi nə olmalıdır?")
])
```

## 🚀 Deployment Options

Yonca AI supports three deployment tiers with the same open-source models:

| Tier | Infrastructure | Cost | Data Location | Performance |
|------|----------------|------|---------------|-------------|
| **Groq Cloud** | Cloud API (benchmark) | $0-50/mo | US | 200-300 tok/s |
| **DigiRella Cloud** | Rented GPU (AzInTelecom) | $800-1,500/mo | 🇦🇿 Azerbaijan | 200-300 tok/s |
| **DigiRella Owned** | Self-hosted hardware | $2,600-145k one-time | Your premises | 200-300 tok/s |

**Key Principle:** Groq demonstrates the benchmark. DigiRella provides the path to replicate that performance with data sovereignty.

📚 **Full Details:**
- [PRICING-SIMPLIFIED.md](docs/PRICING-SIMPLIFIED.md) — Cost comparison & migration path
- [17-DIGIRELLA-HOSTING-PROFILES.md](docs/zekalab/17-DIGIRELLA-HOSTING-PROFILES.md) — Hardware specs
- [16-ALEM-INFRASTRUCTURE-TIERS.md](docs/zekalab/16-ALEM-INFRASTRUCTURE-TIERS.md) — Tier comparison

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

### Testing the API

```bash
# Check chat endpoint info
curl http://localhost:8000/api/v1/chat

# Send a message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Salam! Buğda əkini haqqında məlumat verə bilərsinizmi?",
    "user_id": "farmer_123",
    "stream": false
  }'

# Stream responses
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Pomidor əkini üçün ən yaxşı vaxt nə vaxtdır?",
    "stream": true
  }'
```

## 📄 License

MIT License - ZekaLab © 2026
