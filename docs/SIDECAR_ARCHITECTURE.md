# Yonca AI - Sidecar Intelligence Architecture

## High-Security AgTech Module for Sovereign AI

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SIDECAR INTELLIGENCE ARCHITECTURE                         ║
║                         Yonca Platform v2.0                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  "100% Synthetic Data Pipeline with Ready-to-Plug National Integration"     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 📋 Table of Contents

1. [Level 0 Diagram Logic](#level-0-diagram-logic)
2. [Architecture Components](#architecture-components)
3. [Dummy-to-Real Roadmap](#dummy-to-real-roadmap)
4. [Logical Accuracy Framework](#logical-accuracy-framework)
5. [API Schema](#api-schema)
6. [Deployment Guide](#deployment-guide)

---

## Level 0 Diagram Logic

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           YONCA PLATFORM                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      EXISTING REST API                                │  │
│  │    /api/v1/farms  │  /api/v1/recommendations  │  /api/v1/chatbot    │  │
│  └────────────────────────────┬─────────────────────────────────────────┘  │
│                               │                                             │
│                               │ (No DB Access)                              │
│                               ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              ╔═══════════════════════════════════════╗                │  │
│  │              ║    SIDECAR INTELLIGENCE MODULE        ║                │  │
│  │              ║    /sidecar/recommendations           ║                │  │
│  │              ╚═══════════════════════════════════════╝                │  │
│  │                               │                                       │  │
│  │         ┌─────────────────────┼─────────────────────┐                │  │
│  │         │                     │                     │                │  │
│  │         ▼                     ▼                     ▼                │  │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │  │
│  │  │ PII Gateway │     │ RAG Engine  │     │Lite-Inference│           │  │
│  │  │  (Sanitize) │────▶│  (Qwen2.5)  │◀────│   (GGUF)    │            │  │
│  │  └─────────────┘     └──────┬──────┘     └─────────────┘            │  │
│  │                              │                                       │  │
│  │                              ▼                                       │  │
│  │                    ┌─────────────────┐                              │  │
│  │                    │ Agronomy        │                              │  │
│  │                    │ Rulebook        │                              │  │
│  │                    │ (Deterministic) │                              │  │
│  │                    └─────────────────┘                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    SYNTHETIC DATA LAYER                               │  │
│  │    ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │  │
│  │    │  Weather   │  │   Soil     │  │   Farm     │  │  Scenario  │   │  │
│  │    │ Generator  │  │ Generator  │  │ Profiles   │  │  Farms     │   │  │
│  │    └────────────┘  └────────────┘  └────────────┘  └────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│               ╔═══════════════════════════════════════╗                    │
│               ║         NO DATABASE ACCESS            ║                    │
│               ║    (All data is synthetic/in-memory)  ║                    │
│               ╚═══════════════════════════════════════╝                    │
└─────────────────────────────────────────────────────────────────────────────┘

                              │
                              │ Ready-to-Plug Interface
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   FUTURE: NATIONAL AGRICULTURAL ECOSYSTEM                   │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│    │   ASAN      │  │ AzerStat    │  │ AgriBank    │  │   e-Gov     │     │
│    │  Kənd API   │  │  Data API   │  │ Subsidy API │  │  Identity   │     │
│    └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────┐    ┌───────────────┐    ┌───────────────┐    ┌─────────────┐
│   Farmer    │    │   PII Gateway │    │  RAG Engine   │    │  Response   │
│   Request   │───▶│   (Sanitize)  │───▶│   + Rulebook  │───▶│ (Personal)  │
└─────────────┘    └───────────────┘    └───────────────┘    └─────────────┘
                          │                     │
                          │                     │
                          ▼                     ▼
                   ┌─────────────┐      ┌─────────────┐
                   │  Token Store│      │ Validation  │
                   │ (SHA-256)   │      │   Logs      │
                   └─────────────┘      └─────────────┘
```

**Key Principle:** The Synthetic Engine operates as a **sidecar** - it receives requests through the existing API layer but **never touches the database**. All farm data comes from:
1. Request payload (sanitized)
2. Synthetic generators
3. Pre-defined scenario farms

---

## Architecture Components

### 1. PII-Stripping Gateway

**Purpose:** Zero-trust data sanitization layer

```python
# Location: src/yonca/sidecar/pii_gateway.py

class PIIGateway:
    """
    Flow:
    1. INGEST: Raw request → sanitize() → SanitizedRequest
    2. PROCESS: SanitizedRequest → RAG Engine → SanitizedResponse
    3. EGRESS: SanitizedResponse → personalize() → Final Response
    """
```

**Features:**
- Azerbaijani name pattern detection (e.g., "Əli Məmmədov oğlu")
- Phone number stripping (+994 format)
- GPS coordinate anonymization
- SHA-256 hashing for audit (no original storage)
- Region code mapping (real region → "RGN-XX")

### 2. RAG Engine with Rulebook

**Purpose:** Retrieval-Augmented Generation with deterministic validation

```python
# Location: src/yonca/sidecar/rag_engine.py

class AgronomyRAGEngine:
    """
    Pipeline:
    1. Intent Detection (Azerbaijani → category)
    2. Knowledge Retrieval (semantic search)
    3. Rule Evaluation (deterministic)
    4. LLM Generation (Qwen2.5-7B)
    5. Validation (>90% accuracy target)
    """
```

**Rulebook Categories:**
| Category | Rules | Purpose |
|----------|-------|---------|
| Irrigation | 4 | Water management |
| Fertilization | 3 | Nutrient application |
| Pest Control | 2 | Pest/disease prevention |
| Harvest | 2 | Optimal harvest timing |
| Livestock | 2 | Animal care |
| Soil Management | 2 | pH/nutrient correction |

### 3. Lite-Inference Engine

**Purpose:** Edge-optimized inference for low-bandwidth areas

```python
# Location: src/yonca/sidecar/lite_inference.py

class LiteInferenceEngine:
    """
    Modes:
    - STANDARD: Full Qwen2.5-7B via Ollama
    - LITE: Quantized GGUF (Q4_K_M) - <4.5GB RAM
    - OFFLINE: Pure rule-based - <50ms latency
    """
```

**GGUF Model Options:**
| Model | Quantization | Memory | Speed |
|-------|--------------|--------|-------|
| qwen2.5-7b | Q4_K_M | 4.5GB | 15 tok/s |
| qwen2.5-7b | Q5_K_M | 5.5GB | 12 tok/s |
| qwen2.5-3b | Q4_K_M | 2.0GB | 25 tok/s |
| qwen2.5-1.5b | Q4_K_M | 1.2GB | 40 tok/s |

---

## Dummy-to-Real Roadmap

### 3-Step Technical Transition Plan

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DUMMY-TO-REAL TRANSITION                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PHASE 1: PROTOTYPE (Current)      PHASE 2: HYBRID         PHASE 3: PRODUCTION ║
║  ════════════════════════          ══════════════          ════════════════ ║
║                                                                              ║
║  ┌─────────────────────┐     ┌─────────────────────┐    ┌─────────────────────┐
║  │   100% Synthetic    │     │  Real + Synthetic   │    │    Real Data        │
║  │   Data Pipeline     │────▶│   Data Blending     │───▶│  (PII Protected)    │
║  │                     │     │                     │    │                     │
║  │ • Scenario farms    │     │ • Regional stats    │    │ • ASAN Kənd API     │
║  │ • Generated weather │     │ • Anonymized farms  │    │ • Real telemetry    │
║  │ • Synthetic soil    │     │ • Aggregate IoT     │    │ • Federated learn   │
║  └─────────────────────┘     └─────────────────────┘    └─────────────────────┘
║                                                                              ║
║  Duration: 0-6 months          6-12 months              12-24 months         ║
║  Risk: LOW                     MEDIUM                   HIGH (managed)       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Phase 1: Prototype (Current State)

**Duration:** 0-6 months

**Data Sources:**
- `yonca/data/scenarios.py` - Pre-defined farm profiles
- `yonca/data/generators.py` - Synthetic weather/soil data
- PII Gateway - Ensures no real data leaks

**Integration Points:**
```python
# Current: All data is synthetic
from yonca.data.scenarios import ALL_SCENARIOS
from yonca.data.generators import WeatherGenerator, SoilGenerator
```

**Hot-Swap Interface:**
```python
# src/yonca/sidecar/data_adapter.py (prepared for Phase 2)

class DataAdapter(Protocol):
    """Interface for swappable data sources."""
    
    def get_farm_profile(self, farm_id: str) -> FarmProfile: ...
    def get_weather(self, region: str, days: int) -> list[WeatherData]: ...
    def get_soil_data(self, farm_id: str) -> SoilData: ...
```

### Phase 2: Hybrid (Months 6-12)

**New Data Sources:**
- AzerStat regional agricultural statistics
- Anonymized aggregate farm data (k-anonymity)
- IoT sensor aggregates (non-identifying)

**Code Changes:**
```python
# Phase 2: Blended adapter
class HybridDataAdapter(DataAdapter):
    def __init__(self):
        self.synthetic = SyntheticDataAdapter()
        self.real = SecureRealDataAdapter()  # With PII filtering
    
    def get_weather(self, region: str, days: int) -> list[WeatherData]:
        # Try real data first, fall back to synthetic
        try:
            return self.real.get_weather(region, days)
        except DataUnavailable:
            return self.synthetic.get_weather(region, days)
```

**Security Enhancements:**
- k-anonymity (k ≥ 10) for aggregated data
- Differential privacy for statistics
- Data masking for semi-sensitive fields

### Phase 3: Production (Months 12-24)

**National Ecosystem Integration:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    ASAN Kənd Integration Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  OAuth 2.0   │  │  Data Vault  │  │  Audit Log   │          │
│  │  Identity    │  │  (Encrypted) │  │  (Immutable) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Sidecar Intelligence                         │
│              (Unchanged core architecture)                      │
└─────────────────────────────────────────────────────────────────┘
```

**Federated Learning Option:**
```python
# Phase 3: On-device learning without data leaving farm
class FederatedLearningAdapter:
    """
    Train personalization models on-device.
    Only model gradients (not data) are aggregated.
    """
    def local_train(self, farm_data: LocalData) -> ModelGradients: ...
    def aggregate_gradients(self, gradients: list[ModelGradients]) -> Model: ...
```

---

## Logical Accuracy Framework

### Target: >90% Accuracy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACCURACY ASSURANCE PIPELINE                              │
│                                                                             │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐        │
│   │   LLM     │───▶│ Rulebook  │───▶│  Conflict │───▶│  Final    │        │
│   │  Output   │    │ Validator │    │ Resolver  │    │  Score    │        │
│   └───────────┘    └───────────┘    └───────────┘    └───────────┘        │
│                                                                             │
│   Confidence:       Validation:      Resolution:       Threshold:          │
│   0.5 base         +0.4 if match    +0.1 multi-rule   ≥0.7 accept         │
│                    ×0.5 if conflict  -0.3 no coverage  <0.7 flag          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Validation Logic

```python
# From src/yonca/sidecar/rag_engine.py

def validate_llm_recommendation(self, llm_rec: dict, context: dict) -> tuple[float, list[str]]:
    """
    Cross-reference LLM output against deterministic rulebook.
    
    Scoring:
    - Base LLM confidence: 0.5
    - Rule match bonus: +0.4 (up to rule's confidence_weight)
    - Multi-rule agreement: +0.1
    - No coverage penalty: ×0.7
    - Contradiction penalty: ×0.5
    
    Target: Final score ≥ 0.9 for high-confidence recommendations
    """
```

### Example Validation Flow

```
User Query: "Torpaq nəmliyi 25%, bu gün suvarmaq lazımdır?"
            (Soil moisture 25%, should I irrigate today?)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: LLM Generation                                          │
│ Output: "Bəli, dərhal suvarma lazımdır. Səhər tezdən suvarın." │
│ Base confidence: 0.5                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Rulebook Check                                          │
│ Rule AZ-IRR-001 triggered: moisture < 30% → irrigate           │
│ Rule confidence: 0.95                                           │
│ Match bonus: +0.40                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Context Validation                                      │
│ Check: Is rain expected? No ✓                                   │
│ Check: Is temperature extreme? No ✓                             │
│ No conflicts detected                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Final Score                                             │
│ 0.5 (base) + 0.40 (rule match) = 0.90                          │
│ Status: HIGH CONFIDENCE ✓                                       │
│ Validation: "Matches rule AZ-IRR-001: Critical Low Moisture"   │
└─────────────────────────────────────────────────────────────────┘
```

### Contradiction Handling

```python
# Example: LLM says irrigate, but rain is expected

if "irrigate" in llm_output and context.get("precipitation_expected"):
    # Check rule AZ-IRR-003: Skip irrigation before rain
    score *= 0.5  # Penalize
    notes.append("⚠ May contradict AZ-IRR-003: Rain expected")
```

---

## API Schema

### REST API Endpoints

```
BASE URL: /api/v1/sidecar

┌────────────────────────────────────────────────────────────────────────────┐
│ Endpoint                  │ Method │ Description                          │
├────────────────────────────────────────────────────────────────────────────┤
│ /recommendations          │ POST   │ Get AI recommendations               │
│ /status                   │ GET    │ Service health & stats               │
│ /capabilities             │ GET    │ Current inference mode               │
│ /models                   │ GET    │ Available model info                 │
│ /mode/{mode}              │ POST   │ Switch inference mode                │
│ /rulebook                 │ GET    │ Get agronomy rules                   │
│ /rulebook/categories      │ GET    │ Rule categories                      │
│ /audit                    │ GET    │ PII audit summary                    │
│ /health                   │ GET    │ Health check                         │
└────────────────────────────────────────────────────────────────────────────┘
```

### POST /recommendations - Request Schema

```json
{
  "farm_id": "string (required)",
  "farmer_id": "string (optional)",
  "farmer_name": "string (optional, for personalization)",
  "region": "string (required, e.g., 'Aran', 'Şəki-Zaqatala')",
  "farm_type": "string (required: wheat|vegetable|orchard|livestock|mixed)",
  "crops": ["string"],
  "livestock_types": ["string"],
  "area_hectares": "number (required, >0)",
  "soil_type": "string (optional: clay|sandy|loamy|silty)",
  "soil_moisture_percent": "integer (0-100)",
  "soil_ph": "number (0-14)",
  "nitrogen_level": "number (kg/ha)",
  "phosphorus_level": "number (kg/ha)",
  "potassium_level": "number (kg/ha)",
  "temperature_min": "number (°C)",
  "temperature_max": "number (°C)",
  "precipitation_expected": "boolean",
  "humidity_percent": "integer (0-100)",
  "query": "string (user question in Azerbaijani/English)",
  "language": "string (default: 'az')",
  "max_recommendations": "integer (default: 5, max: 20)",
  "include_rulebook_refs": "boolean (default: true)",
  "inference_mode": "string (optional: standard|lite|offline)"
}
```

### POST /recommendations - Response Schema

```json
{
  "request_id": "string",
  "farm_id": "string",
  "recommendations": [
    {
      "id": "string",
      "type": "string (irrigation|fertilization|pest_control|...)",
      "priority": "string (critical|high|medium|low)",
      "confidence": "number (0.0-1.0)",
      "title": "string",
      "title_az": "string",
      "description": "string",
      "description_az": "string",
      "source": "string (llm|rulebook|hybrid)",
      "rule_id": "string (if from rulebook)",
      "suggested_time": "string (optional)",
      "estimated_duration_minutes": "integer (optional)"
    }
  ],
  "overall_confidence": "number (0.0-1.0)",
  "accuracy_score": "number (0.0-1.0, target >0.9)",
  "validation_notes": ["string"],
  "inference_mode": "string (standard|lite|offline)",
  "model_version": "string",
  "processing_time_ms": "integer",
  "generated_at": "datetime",
  "valid_until": "datetime"
}
```

### GraphQL Schema

```graphql
type Query {
  recommendations(input: RecommendationInput!): RecommendationResponse!
  rulebook(category: String): [AgronomyRule!]!
  capabilities: InferenceCapability!
  status: ServiceStatus!
}

input RecommendationInput {
  farmId: String!
  region: String!
  farmType: String!
  crops: [String!]
  areaHectares: Float!
  query: String
  language: String = "az"
  soilMoisturePercent: Int
  temperatureMax: Float
  precipitationExpected: Boolean = false
}

type RecommendationResponse {
  requestId: String!
  farmId: String!
  recommendations: [RecommendationItem!]!
  overallConfidence: Float!
  accuracyScore: Float!
  inferenceMode: String!
  modelVersion: String!
  processingTimeMs: Int!
}

type RecommendationItem {
  id: String!
  type: String!
  priority: Priority!
  confidence: Float!
  title: String!
  titleAz: String!
  description: String!
  descriptionAz: String!
  source: String!
  ruleId: String
}

type AgronomyRule {
  ruleId: String!
  name: String!
  nameAz: String!
  category: String!
  description: String!
  descriptionAz: String!
  recommendation: String!
  recommendationAz: String!
  confidenceWeight: Float!
}

enum Priority {
  CRITICAL
  HIGH
  MEDIUM
  LOW
}
```

---

## Deployment Guide

### Quick Start

```bash
# 1. Install dependencies
poetry install --all-extras

# 2. Start Ollama with Qwen2.5
ollama pull qwen2.5:7b

# 3. Run Yonca with Sidecar
python -m yonca.startup
```

### Integration with Existing Routes

```python
# In src/yonca/main.py, add:

from yonca.sidecar.api_routes import router as sidecar_router

app.include_router(sidecar_router)
```

### Edge Deployment

```python
from yonca.sidecar.lite_inference import EdgeDeploymentConfig, create_lite_engine_for_edge

# Configure for rural edge device
config = EdgeDeploymentConfig(
    max_memory_mb=2000,
    has_gpu=False,
    expected_bandwidth_kbps=256,
    is_intermittent=True,
)

engine = create_lite_engine_for_edge(config)
```

### Environment Variables

```bash
# .env file
YONCA_DEBUG=false
YONCA_DEFAULT_LANGUAGE=az
YONCA_RECOMMENDATION_CONFIDENCE_THRESHOLD=0.7

# Ollama configuration
OLLAMA_HOST=http://localhost:11434

# Sidecar configuration
SIDECAR_INFERENCE_MODE=auto  # auto|standard|lite|offline
SIDECAR_ENABLE_AUDIT_LOG=true
SIDECAR_GGUF_MODEL=qwen2.5-7b-q4
```

---

## Security Considerations

### PII Protection Summary

| Data Type | Treatment | Storage |
|-----------|-----------|---------|
| Farmer Name | Stripped → `[ŞƏXS_1]` | Never stored |
| Phone | Stripped → `[TELEFON]` | SHA-256 hash only |
| GPS Coords | Stripped → `[KOORDİNAT]` | Region code only |
| Farm ID | Anonymized → `syn_abc123` | Token mapping |
| Soil Data | Passed through | No PII risk |
| Weather | Passed through | Regional aggregate |

### Audit Trail

```python
# Audit log entry (hashes only, no PII)
{
    "timestamp": "2026-01-16T10:30:00",
    "request_id": "req_abc123",
    "pii_fields_detected": 3,
    "field_types": ["name", "phone", "coordinates"]
}
```

---

## Strategic Enhancements

### Overview

The Sidecar Intelligence Architecture includes five strategic enhancement modules that address critical "blind spots" in traditional AgTech AI systems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STRATEGIC ENHANCEMENT MODULES                            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Agronomist     │  │    Dialect      │  │   Temporal      │            │
│  │  in-the-Loop    │  │    Handler      │  │   State Mgmt    │            │
│  │   Validation    │  │  (Multilingual) │  │  (Farm Memory)  │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                     │                     │
│           └────────────────────┼─────────────────────┘                     │
│                                │                                           │
│                    ┌───────────┴───────────┐                              │
│                    │    Core Sidecar       │                              │
│                    │     RAG Engine        │                              │
│                    └───────────┬───────────┘                              │
│                                │                                           │
│           ┌────────────────────┼────────────────────┐                     │
│           │                    │                    │                     │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌──────┴──────────┐          │
│  │  Trust Score    │  │  Digital Twin   │  │  Enhanced       │          │
│  │  & Citations    │  │   Simulator     │  │  API Response   │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Agronomist-in-the-Loop Validation

**Location:** `src/yonca/sidecar/validation.py`

**Purpose:** Human expert validation system ensuring AI recommendations are verified before reaching farmers.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    THREE-TIER VALIDATION SYSTEM                           │
│                                                                           │
│  TIER 1: AUTOMATIC          TIER 2: ASYNC REVIEW     TIER 3: SYNC REVIEW │
│  ══════════════════         ═══════════════════       ═════════════════  │
│                                                                           │
│  ┌───────────────┐         ┌───────────────┐         ┌───────────────┐  │
│  │ Pre-Approved  │         │ Expert Queue  │         │  Real-Time    │  │
│  │ Rules Match   │         │ <24h Review   │         │  Approval     │  │
│  │ >90% Conf.    │         │ High Priority │         │  Required     │  │
│  └───────────────┘         └───────────────┘         └───────────────┘  │
│         │                         │                         │           │
│         ▼                         ▼                         ▼           │
│  ✅ Auto-Approved          ⏳ Pending Review         🔒 Blocked         │
│  Badge: "✓ Expert          Badge: "⏳ Pending        Until Expert       │
│         Verified"                  Review"           Approves           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Demo Agronomist Profiles:**
| Expert | Specialization | Region | Degree |
|--------|----------------|--------|--------|
| Dr. Elçin Məmmədov | Irrigation, Soil | Aran | Ph.D |
| Prof. Aynur Həsənova | Crops, Pest Control | Şəki | Professor |
| Fərid Əliyev | Livestock, Organic | All | M.Sc |

### 2. Dialect & Regional Term Handler

**Location:** `src/yonca/sidecar/dialect.py`

**Purpose:** Linguistic normalization for Azerbaijani agricultural terminology across regional dialects.

**Supported Dialects:**
- **Standard (Bakı)** - Official/technical vocabulary
- **Aran** - Lowland agricultural region
- **Şəki-Zaqatala** - Mountain region
- **Lənkəran** - Southern region
- **Naxçıvan** - Autonomous region
- **Quba-Xaçmaz** - Northern region
- **Gəncə-Qazax** - Western region

**Example Term Mappings:**

| Standard (Technical) | English | Aran | Şəki-Zaqatala | Lənkəran |
|---------------------|---------|------|---------------|----------|
| suvarma | irrigation | su vermə | su çəkmə | sulamaq |
| gübrə | fertilizer | gübrə | kübrə | güvrə |
| zərərverici | pest | həşərat | ziyanlı | zərər verən |
| məhsul | harvest | biçin | hösul | yığma |
| torpaq | soil | yer | torpağ | torpaq |

**Workflow:**
```
Farmer Input (Regional) → normalize() → Standard Azerbaijani → AI Processing
                                                                    │
AI Response (Standard) → localize() → Farmer's Dialect ◄───────────┘
```

### 3. Temporal State Management

**Location:** `src/yonca/sidecar/temporal.py`

**Purpose:** Farm timeline memory for contextual recommendations.

> *"Agriculture is not a static chat; it is a timeline."*

**Features:**
- Track past actions (irrigation, fertilization, spraying)
- Season-aware context (Azerbaijan agricultural calendar)
- Intelligent timing warnings
- Pending action reminders

**Action Tracking:**
```python
# The AI remembers farm history
recent_context = manager.get_relevant_context(
    action_type=ActionType.FERTILIZATION,
    crop="buğda",
    days_lookback=30
)
# Returns: "15 days ago: fertilization for wheat"
```

**Timing Intelligence:**
```
⚠️ Diqqət: buğda üçün son suvarma 3 gün əvvəl edilib.
   Növbəti suvarma üçün daha 4 gün gözləmək tövsiyə olunur.
```

**Seasonal Awareness:**
| Season Phase | Months | Key Activities |
|--------------|--------|----------------|
| Early Spring | Feb-Mar | Spring planting prep |
| Late Spring | Apr-May | Pest monitoring |
| Early Summer | Jun-Jul | Peak irrigation |
| Late Summer | Aug-Sep | Harvest begins |
| Early Autumn | Oct-Nov | Winter crop planting |
| Winter | Dec-Feb | Pruning, planning |

### 4. Trust Score & Citation System

**Location:** `src/yonca/sidecar/trust.py`

**Purpose:** Full transparency with confidence scores and source citations.

**Confidence Breakdown:**
```
🎯 Etibarlılıq: 87% - 🟢 Yüksək Etibarlılıq

📊 Təhlil:
  • Qayda uyğunluğu: 95%
  • Mənbə keyfiyyəti: 90%
  • Ekspert təsdiqi: 70%
  • Mövsüm uyğunluğu: 85%
  • Bölgə uyğunluğu: 80%

📚 Mənbələr:
  1. 📘 Yonca Suvarma Təlimatı, v2.1
  2. 🏛️ Azərbaycan Kənd Təsərrüfatı Standartları
  3. 🌤️ Milli Hidrometeorologiya Xidməti
```

**Citation Library:**
| Source ID | Type | Title |
|-----------|------|-------|
| AZ-IRR-001 | Rulebook | Yonca Suvarma Təlimatı |
| AZ-FERT-001 | Rulebook | Yonca Gübrələmə Standartları |
| GOV-AG-2024 | Government | Azərbaycan Kənd Təsərrüfatı Standartları |
| WHEAT-GUIDE-V2 | Guideline | Yonca Buğda Bələdçisi |
| AZ-METEO | Weather | Milli Hidrometeorologiya Xidməti |

### 5. Digital Twin Simulation Engine

**Location:** `src/yonca/sidecar/digital_twin.py`

**Purpose:** Strategic rebranding of "Dummy Data" to "Digital Twin Scenarios" with simulation capabilities.

> *A Digital Twin is a virtual replica of a farm that can simulate conditions without affecting real operations.*

**Simulation Modes:**
| Mode | Use Case | Yield Impact | Risk Level |
|------|----------|--------------|------------|
| BASELINE | Normal conditions | 100% | Low |
| OPTIMAL | Best-case scenario | 125% | Very Low |
| DROUGHT_STRESS | Water scarcity | 65% | High |
| PEST_OUTBREAK | Infestation scenario | 70% | High |
| CLIMATE_EXTREME | Weather events | 55% | Critical |
| WORST_CASE | Risk assessment | 40% | Critical |

**Simulation Output Example:**
```
🌱 Rəqəmsal Əkiz Simulyasiya Nəticələri
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Bölgə: Aran
🌾 Bitki: buğda
📐 Sahə: 10 hektar
📅 Müddət: 180 gün

📊 Məhsul Proqnozu:
  • Gözlənilən məhsul: 3,500 kq/ha
  • Etibarlılıq aralığı: 2,975-4,025 kq/ha
  • Bölgə ortalaması ilə: +16.7%

💰 Maliyyə Proqnozu:
  • Gözlənilən gəlir: 15,750 AZN
  • Xərclər: 7,500 AZN
  • Mənfəət: 8,250 AZN
  • ROI: 110.0%

⚠️ Risk Qiymətləndirməsi: 🟢 Aşağı (25%)
```

**Scenario Comparison:**
```
📊 Ssenari Müqayisəsi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ssenari         Məhsul       Mənfəət      Risk
────────────────────────────────────────────────────────────
baseline        3,500 kq/ha  8,250 AZN    25%   ◄
optimal         4,375 kq/ha  12,188 AZN   15%
drought         2,275 kq/ha  2,738 AZN    70%
worst_case      1,400 kq/ha  -2,100 AZN   95%
```

---

## Enhancement API Endpoints

### New Endpoints for Strategic Features

```
BASE URL: /api/v1/sidecar

┌────────────────────────────────────────────────────────────────────────────┐
│ ENHANCEMENT ENDPOINTS                                                      │
├────────────────────────────────────────────────────────────────────────────┤
│ /validation/queue          │ GET    │ View pending expert reviews         │
│ /validation/{id}/approve   │ POST   │ Expert approval endpoint            │
│ /validation/{id}/reject    │ POST   │ Expert rejection endpoint           │
│ /dialect/normalize         │ POST   │ Normalize regional terms            │
│ /dialect/localize          │ POST   │ Convert to regional dialect         │
│ /temporal/{session}/context│ GET    │ Get farm timeline context           │
│ /temporal/{session}/action │ POST   │ Record a farm action                │
│ /trust/{rec_id}/report     │ GET    │ Full transparency report            │
│ /simulation/run            │ POST   │ Run Digital Twin simulation         │
│ /simulation/compare        │ POST   │ Compare multiple scenarios          │
└────────────────────────────────────────────────────────────────────────────┘
```

### Enhanced Recommendation Response

```json
{
  "request_id": "string",
  "recommendations": [...],
  
  // NEW: Strategic Enhancement Fields
  "trust_score": {
    "overall_confidence": 0.87,
    "confidence_level": "high",
    "breakdown": {
      "rule_match_score": 0.95,
      "source_quality_score": 0.90,
      "expert_validation_score": 0.70,
      "temporal_relevance_score": 0.85,
      "regional_relevance_score": 0.80
    },
    "citations": [
      {
        "source_id": "AZ-IRR-001",
        "title": "Yonca Suvarma Təlimatı",
        "version": "2.1"
      }
    ],
    "primary_source": "AZ-IRR-001"
  },
  
  "validation_status": {
    "tier": "automatic",
    "status": "verified",
    "badge": "✓ Expert Verified",
    "expert": null
  },
  
  "temporal_context": {
    "last_irrigation_days_ago": 5,
    "last_fertilization_days_ago": 12,
    "current_season": "late_spring",
    "reminders": [
      "💧 buğda suvarma vaxtı yaxınlaşır"
    ]
  },
  
  "dialect_info": {
    "detected_dialect": "aran",
    "normalized_query": "...",
    "localized_response": true
  }
}
```

---

## Contact & Support

- **Repository:** https://github.com/Px8Studio/yonja
- **Documentation:** `/docs/SIDECAR_ARCHITECTURE.md`
- **API Docs:** `/docs/api/openapi.json`

---

*Built with 🌿 for Azerbaijan's agricultural future*
