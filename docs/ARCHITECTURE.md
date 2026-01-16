# Yonca AI - Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              YONCA AI PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Mobile App  │    │   Web App    │    │  Yonca Main  │                  │
│  │  (Offline)   │    │              │    │   Platform   │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                    │                          │
│         └───────────────────┼────────────────────┘                          │
│                             │                                               │
│                    ┌────────▼────────┐                                      │
│                    │   API Gateway   │                                      │
│                    │  REST/GraphQL   │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                    │
│  │  Chatbot    │    │ Recommend.  │    │  Scheduler  │                    │
│  │  Engine     │    │   Engine    │    │   Service   │                    │
│  │  (AZ/EN)    │    │ (AI Rules)  │    │             │                    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                    │
│         │                   │                   │                          │
│         └───────────────────┼───────────────────┘                          │
│                             │                                               │
│                    ┌────────▼────────┐                                      │
│                    │   Rule Engine   │                                      │
│                    │   (Decision     │                                      │
│                    │    Trees)       │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                    │
│  │  Synthetic  │    │   Weather   │    │   Offline   │                    │
│  │    Data     │    │  Simulator  │    │   Storage   │                    │
│  │  Generator  │    │             │    │  (SQLite)   │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer

**REST API** (`/api/v1/`)
- `GET /farms` - List all farm profiles
- `GET /farms/{id}` - Get specific farm
- `POST /recommendations` - Get AI recommendations
- `GET /farms/{id}/schedule` - Get daily schedule
- `POST /chatbot/message` - Chat with AI assistant
- `GET /alerts/today` - Get today's alerts
- `GET /weather/{region}` - Get weather forecast

**GraphQL** (`/graphql`)
- Query: farms, farm, farmRecommendations, dailySchedule, weatherForecast
- Mutation: sendChatMessage

### 2. Recommendation Engine

The core AI logic uses **rule-based decision trees**:

```
                    ┌─────────────────┐
                    │   Farm Profile  │
                    │   + Weather     │
                    │   + Soil Data   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Rule Evaluator │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
   ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
   │ Irrigation│      │Fertilizer │      │   Pest    │
   │   Rules   │      │   Rules   │      │  Control  │
   └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Prioritization │
                    │   & Scoring     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Recommendations │
                    └─────────────────┘
```

### 3. Rule Categories

| Category | Rule Count | Priority Range |
|----------|-----------|----------------|
| Irrigation | 4 | Critical - Medium |
| Fertilization | 4 | High - Low |
| Pest/Disease | 3 | High - Medium |
| Harvest | 2 | Critical |
| Livestock | 4 | Critical - Medium |
| Subsidy | 1 | High |

### 4. Chatbot Architecture

**Intent-Based NLU**

```
User Input (AZ) → Pattern Matching → Intent Classification
                                            │
                                    ┌───────▼───────┐
                                    │ Intent Router │
                                    └───────┬───────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        │              │              │              │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │ suvarma │   │ gübrə   │   │xəstəlik │   │ məhsul  │   │  hava   │   │ cədvəl  │
   │ sorğusu │   │ sorğusu │   │xəbərdarlığı│ │ yığımı  │   │ sorğusu │   │ sorğusu │
   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘
        │              │              │              │              │              │
        └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
                                            │
                                    ┌───────▼───────┐
                                    │   Response    │
                                    │   Generator   │
                                    └───────────────┘
```

**Supported Intents:**
- `greeting` - Salam, hello
- `suvarma_sorğusu` - Irrigation queries
- `gübrələmə_sorğusu` - Fertilization queries
- `xəstəlik_xəbərdarlığı` - Disease/pest alerts
- `məhsul_yığımı` - Harvest timing
- `hava_sorğusu` - Weather information
- `heyvan_sorğusu` - Livestock care
- `subsidiya_sorğusu` - Subsidy info
- `cədvəl_sorğusu` - Daily schedule
- `kömək` - Help
- `vidalaşma` - Goodbye

### 5. Offline Support

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
