# 🌿 Yonca AI - Headless Intelligence as a Service

> **Sidecar Intelligence Engine** for the Yonca agricultural platform.
> High-security, edge-ready AI backend with REST/GraphQL APIs, PII protection, and Azerbaijani language support.

## 🎯 Overview

Yonca AI is a **Headless Intelligence as a Service** backend—a detached, high-performance AI module that integrates seamlessly with existing platforms via API. Built with a "Logic-First" methodology, it delivers deterministic, rule-validated farm recommendations using 100% synthetic data.

**Key Architecture Principles:**
- **Sidecar Model**: Standalone AI engine that never touches core platform systems
- **Data Sovereignty**: 100% synthetic datasets—zero legal/operational friction
- **Edge-Ready**: Lightweight inference with Qwen2.5-7B for low-connectivity zones
- **Logic-First**: Deterministic agronomy rulebook overrides LLM hallucinations

## ✨ Features

- **PII Gateway** - Zero-trust data sanitization layer
- **RAG Engine** - Retrieval-Augmented Generation with agronomy rulebook
- **Lite Inference** - Edge-optimized GGUF quantization support
- **Rules Registry** - Deterministic agronomy rules with AZ- prefixes
- **Multi-LLM Support** - Google Gemini (cloud) or Qwen2.5 via Ollama (local)
- **Azerbaijani Language** - Native language support with Turkic dialect normalization
- **Trust Scores** - Confidence scoring with source citations
- **Digital Twin** - Simulation engine for scenario planning
- **REST & GraphQL APIs** - Flexible headless integration options
- **100% Synthetic Data** - Complete data safety, no real farmer data

## 🏗️ Architecture

```
yonca-ai/
├── src/
│   └── yonca/
│       ├── sidecar/          # 🎯 CORE: Sidecar Intelligence Engine
│       │   ├── pii_gateway   # Zero-trust data sanitization
│       │   ├── rag_engine    # Retrieval-augmented generation
│       │   ├── rules_registry# Deterministic agronomy rules
│       │   ├── intent_matcher# Azerbaijani intent detection
│       │   ├── lite_inference# Edge-ready LLM inference
│       │   ├── trust         # Confidence scoring
│       │   └── digital_twin  # Farm simulation
│       ├── api/              # REST & GraphQL endpoints
│       ├── agent/            # LangGraph AI orchestration
│       ├── data/             # Synthetic scenarios & generators
│       ├── models/           # Pydantic data models
│       └── startup.py        # Startup with Ollama health checks
├── tests/                    # Test suite
└── docs/                     # Documentation & API specs
```

## 🚀 Quick Start

### Prerequisites

#### Option A: Local LLM with Ollama (Recommended for Azerbaijani 🇦🇿)

**Ollama is required for running local AI models.** This gives you:
- ✅ 100% offline capability
- ✅ No API costs
- ✅ Data never leaves your machine
- ✅ Best Azerbaijani language support with Qwen2.5

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

```bash
# Clone the repository
git clone https://github.com/ZekaLab/yonja.git
cd yonja

# Create virtual environment (Python 3.12)
python -m venv .venv312
.venv312\Scripts\activate  # Windows
source .venv312/bin/activate  # Linux/Mac

# Install with your preferred LLM provider
pip install -e ".[ollama]"    # For local Qwen2.5
pip install -e ".[gemini]"    # For Google Gemini
pip install -e ".[all-llms]"  # Both options
pip install -e ".[dev]"       # Development tools
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
✅ Model qwen2.5:7b ready

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     🌿 Yonca AI Status             ┃
┣━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Component  ┃ Status                ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Ollama     │ ✅ Running            │
│ LLM Model  │ ✅ qwen2.5:7b         │
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
| **Ollama** | `qwen2.5:7b` | 4.7GB | 🇦🇿 Azerbaijani (Recommended) |
| **Ollama** | `qwen2.5:3b` | 2.0GB | Fast responses, limited RAM |
| **Ollama** | `qwen2.5:14b` | 9.0GB | Highest quality |
| **Gemini** | `gemini-2.0-flash` | Cloud | Production, high volume |
| **Gemini** | `gemini-1.5-pro` | Cloud | Complex reasoning |

### Usage Example

```python
from yonca.agent import create_ollama_agent, create_gemini_agent

# Local Ollama (Azerbaijani-optimized)
agent = create_ollama_agent(model="qwen2.5:7b")
response = agent.chat("Buğda sahəsini nə vaxt suvarmaq lazımdır?")

# Google Gemini (Cloud)
agent = create_gemini_agent(api_key="your-key", model="gemini-2.0-flash")
response = agent.chat("Torpağın pH səviyyəsi nə olmalıdır?")
```

## 📡 API Endpoints

### REST API
```
POST /api/v1/recommendations     # Get AI recommendations
GET  /api/v1/farm/{id}/schedule  # Get daily schedule
POST /api/v1/chatbot/message     # Chat with assistant
GET  /api/v1/alerts/today        # Get today's alerts
```

### GraphQL
```graphql
query {
  farmRecommendations(farmId: "farm-001") {
    tasks { title priority dueDate }
    alerts { type severity message }
  }
}
```

## 🧪 Testing

```bash
pytest tests/ -v --cov=src/yonca
```

## 📄 License

MIT License - ZekaLab © 2026

## 🤝 Contributing

This is a prototype demonstration. For integration with the Yonca platform, contact ZekaLab.
