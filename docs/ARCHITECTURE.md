# Yonca AI - Technical Architecture

> **Goal:** Deliver rule-validated, Azerbaijani-language farm recommendations via a headless API.

## 🎯 Core Principle: The Sidecar Model

```
┌────────────────────────────────────────────────────────────────────────┐
│                        YONCA PLATFORM (Digital Umbrella)               │
│                                                                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                  │
│  │ Mobile App  │   │  EKTIS API  │   │ Subsidy Sys │  ← Existing      │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                  │
│         │                 │                 │                          │
│         └─────────────────┼─────────────────┘                          │
│                           │ (We don't touch this)                      │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   🌿 YONCA AI SIDECAR (This Repo)                      │
│                                                                        │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │                      REST/GraphQL API                         │   │
│    │         /api/v1/recommendations  /api/v1/chatbot             │   │
│    └─────────────────────────┬────────────────────────────────────┘   │
│                              │                                         │
│    ┌─────────────────────────┼─────────────────────────────────────┐  │
│    │              SIDECAR INTELLIGENCE ENGINE                       │  │
│    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│    │  │  Intent  │  │  Rules   │  │ Schedule │  │   Lite   │      │  │
│    │  │ Matcher  │→ │ Registry │→ │ Service  │→ │Inference │      │  │
│    │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│    └───────────────────────────────────────────────────────────────┘  │
│                              │                                         │
│    ┌─────────────────────────┼─────────────────────────────────────┐  │
│    │              SYNTHETIC DATA (No Real Farmer Data)              │  │
│    │    🌾 Wheat   🐄 Livestock   🍎 Orchard   🥬 Vegetable        │  │
│    └───────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

**Why Sidecar?** 
- Digital Umbrella's core systems handle legal/financial data (subsidies)
- We can't touch that—so we run alongside as a recommendation-only layer
- Future: Ready to plug into real data hooks without code changes

---

## Component Details

### 1. Sidecar Modules (The Core)

| Module | File | Purpose |
|--------|------|---------|
| **Rules Registry** | `rules_registry.py` | Single source of truth: 20+ agronomy rules with `AZ-` prefixes |
| **Intent Matcher** | `intent_matcher.py` | Pattern-based Azerbaijani NLU (suvarma, gübrə, hava, etc.) |
| **Schedule Service** | `schedule_service.py` | Generates daily task lists with priorities and times |
| **Recommendation Service** | `recommendation_service.py` | Orchestrates the full pipeline |
| **Lite Inference** | `lite_inference.py` | 3 modes: `standard` / `lite` / `offline` |
| **PII Gateway** | `pii_gateway.py` | Strips personal data before LLM processing |
| **Trust** | `trust.py` | Computes confidence scores with rule citations |

### 2. Data Flow (Recommendation Request)

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ API Request │ → │ PII Gateway │ → │   Rules     │ → │  Response   │
│ (farm_id,   │   │ (sanitize)  │   │  Registry   │   │ (tasks +    │
│  query)     │   │             │   │  + LLM      │   │  citations) │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

### 3. API Layer

**REST API** (`/api/v1/`)
```
GET  /farms              → List 7 synthetic farm profiles
GET  /farms/{id}         → Get specific farm
POST /recommendations    → Get AI recommendations
GET  /farms/{id}/schedule → Get daily task schedule
POST /chatbot/message    → Chat in Azerbaijani
GET  /alerts/today       → Get weather/disease alerts
```

**Sidecar API** (`/api/v1/sidecar/`)
```
POST /recommendations    → Full sidecar pipeline with PII gateway
GET  /status             → Service health + inference mode
POST /mode/{mode}        → Switch inference: standard/lite/offline
GET  /rulebook           → View agronomy rules
```

### 4. Inference Modes

| Mode | Engine | Speed | Use Case |
|------|--------|-------|----------|
| `standard` | Qwen2.5-7B via Ollama | ~15 tok/s | Full LLM + rules |
| `lite` | Quantized GGUF (Q4_K_M) | ~25 tok/s | Edge devices, <4.5GB RAM |
| `offline` | Rules only, no LLM | <50ms | No network, always works |

### 5. Supported Intents (Azerbaijani)

| Intent | Keywords | Example |
|--------|----------|---------|
| `suvarma` | suvar, su, irrigation | "Nə vaxt suvarmalıyam?" |
| `gübrələmə` | gübrə, fertilizer | "Gübrə lazımdırmı?" |
| `xəstəlik` | xəstə, pest, disease | "Bitkilər xəstədir" |
| `məhsul_yığımı` | yığım, harvest | "Məhsulu nə vaxt yığım?" |
| `hava` | hava, weather | "Bu həftə hava necə olacaq?" |
| `cədvəl` | cədvəl, plan, schedule | "Bu gün nə etməliyəm?" |

**SQLite-based storage for low-connectivity:**

```sql
-- Cache table
CREATE TABLE cache (
    key TEXT PRIMARY KEY,
    data TEXT,
    created_at TEXT,
    expires_at TEXT,
    checksum TEXT
);

-- Sync queue
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY,
    operation TEXT,
    entity_type TEXT,
    entity_id TEXT,
    data TEXT,
    synced INTEGER DEFAULT 0
);

-- Local farms cache
CREATE TABLE farms (
    id TEXT PRIMARY KEY,
    data TEXT,
    last_updated TEXT
);

-- Recommendations cache
CREATE TABLE recommendations (
    id TEXT PRIMARY KEY,
    farm_id TEXT,
    data TEXT,
    date TEXT
);

-- Chat history
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    user_message TEXT,
    bot_response TEXT,
    intent TEXT
);
```

### 6. Data Flow

```
1. User Request
        │
        ▼
2. Check Offline Cache
        │
   ┌────┴────┐
   │         │
   ▼         ▼
 Cache     Online
  Hit      Request
   │         │
   │         ▼
   │    API Server
   │         │
   │         ▼
   │    Rule Engine
   │         │
   │         ▼
   │    Generate
   │    Recommendations
   │         │
   │         ▼
   │    Update Cache
   │         │
   └────┬────┘
        │
        ▼
3. Return Response
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.10+ | Core application |
| Framework | FastAPI | REST API |
| GraphQL | Strawberry | GraphQL API |
| Data Models | Pydantic | Validation |
| Database | SQLite | Offline storage |
| Testing | Pytest | Test suite |

## Integration Points

### Yonca Platform Integration

The AI module can be integrated via:

1. **REST API Plugin**
   ```python
   # Yonca backend calls Yonca AI
   response = requests.post(
       "http://yonca-ai/api/v1/recommendations",
       json={"farm_id": farmer.farm_id}
   )
   ```

2. **Direct Import**
   ```python
   from yonca.core.engine import recommendation_engine
   
   recommendations = recommendation_engine.generate_recommendations(farm)
   ```

3. **GraphQL Federation**
   - Extend Yonca's GraphQL schema with AI types
   - Federated queries across services

## Scalability Considerations

1. **Horizontal Scaling**
   - Stateless API design
   - Can run multiple instances behind load balancer

2. **Caching Strategy**
   - Redis for production caching
   - Local SQLite for offline

3. **Future ML Integration**
   - Rule engine designed to be replaceable
   - Can swap rules for trained models
   - Interface remains the same

## Security

- **100% Synthetic Data** - No real farmer data
- **Input Validation** - Pydantic models
- **CORS Configuration** - Configurable origins
- **Rate Limiting** - Can be added at API gateway
