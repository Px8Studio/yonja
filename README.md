# 🌿 Yonca AI - Smart Farm Planning Assistant

An AI-driven daily farm planning assistant prototype for the Yonca agricultural platform.

## 🎯 Overview

Yonca AI provides intelligent recommendations for daily farm operations using rule-based AI logic and synthetic datasets. Built to demonstrate the next evolution of personalized, intelligent farm assistance without requiring real farmer data.

## ✨ Features

- **AI Recommendation Engine** - Rule-based advisory system for farming decisions
- **5+ Farm Scenarios** - Wheat, Livestock, Orchard, Vegetable, Mixed farming profiles
- **Azerbaijani Chatbot** - Intent-based assistant in native language
- **Offline Support** - Works in low-connectivity environments
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

### Installation

```bash
# Clone the repository
git clone https://github.com/Px8Studio/yonja.git
cd yonja

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"
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
