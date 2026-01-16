# 🌿 Yonca AI - Smart Farm Planning Assistant

An AI-driven daily farm planning assistant prototype for the Yonca agricultural platform.

## 🎯 Overview

Yonca AI provides intelligent recommendations for daily farm operations using **LangGraph-powered AI agents** and synthetic datasets. Built to demonstrate the next evolution of personalized, intelligent farm assistance without requiring real farmer data.

## ✨ Features

- **LangGraph AI Agent** - Intelligent orchestration with tool-calling capabilities
- **Multi-LLM Support** - Google Gemini (cloud) or Qwen2.5 via Ollama (local)
- **Azerbaijani Language** - Native language support with Qwen2.5's Turkic optimization
- **5+ Farm Scenarios** - Wheat, Livestock, Orchard, Vegetable, Mixed farming profiles
- **Offline Support** - Works in low-connectivity environments with local LLM
- **REST & GraphQL APIs** - Flexible integration options
- **100% Synthetic Data** - Complete data safety, no real farmer data

## 🏗️ Architecture

```
yonca-ai/
├── src/
│   └── yonca/
│       ├── api/              # REST & GraphQL endpoints
│       ├── core/             # Business logic
│       │   ├── engine/       # Recommendation engine
│       │   ├── rules/        # Rule definitions
│       │   └── scheduler/    # Task scheduling
│       ├── chatbot/          # Azerbaijani chatbot
│       ├── data/             # Synthetic data & generators
│       └── models/           # Data models
├── tests/                    # Test suite
└── docs/                     # Documentation
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

**Download the Qwen2.5 model** (best for Azerbaijani/Turkic languages):

```bash
# Restart terminal after Ollama install, then:
ollama pull qwen2.5:7b    # 4.7GB - Best balance of speed & quality
# OR
ollama pull qwen2.5:3b    # 2.0GB - Faster, lighter
ollama pull qwen2.5:14b   # 9.0GB - Highest quality
```

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
git clone https://github.com/Px8Studio/yonja.git
cd yonja

# Create virtual environment (Python 3.12 recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install with your preferred LLM provider
pip install -e ".[ollama]"    # For local Qwen2.5
pip install -e ".[gemini]"    # For Google Gemini
pip install -e ".[all-llms]"  # Both options
pip install -e ".[dev]"       # Development tools
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your preferred LLM settings
```

### Run the API Server

```bash
uvicorn src.yonca.main:app --reload
```

### Access the API

- REST API: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql

## 📊 Farm Scenarios

| Profile | Description | Key Recommendations |
|---------|-------------|---------------------|
| 🌾 Wheat | Grain production | Irrigation, fertilization, harvest timing |
| 🐄 Livestock | Animal husbandry | Feeding schedules, health monitoring |
| 🍎 Orchard | Fruit trees | Pruning, pest control, harvest planning |
| 🥬 Vegetable | Intensive crops | Rotation, irrigation, pest management |
| 🌿 Mixed | Combined farming | Integrated planning across domains |

## 🤖 Chatbot Intents (Azerbaijani)

- `suvarma_sorğusu` - Irrigation advice
- `gübrələmə_sorğusu` - Fertilization recommendations
- `xəstəlik_xəbərdarlığı` - Disease/pest alerts
- `məhsul_yığımı` - Harvest planning
- `subsidiya_tarixi` - Subsidy deadlines

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

MIT License - Digital Umbrella © 2026

## 🤝 Contributing

This is a prototype demonstration. For integration with the Yonca platform, contact Digital Umbrella.
