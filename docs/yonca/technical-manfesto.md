# Yonca AI - Technical Manifesto

> **The North Star:** Build a **Headless AI Sidecar** that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 🎯 Ultimate Goal

**Create a production-ready AI farm planning assistant** that:
1. **Runs 100% offline** on edge devices (farmer's phone or local server)
2. **Speaks native Azerbaijani** with dialect support  
3. **Uses deterministic agronomy rules** to override LLM hallucinations (≥90% logical accuracy)
4. **Protects farmer data** via PII gateway (zero real data in AI pipeline)
5. **Plugs into Yonca platform** without touching existing EKTIS/subsidy systems

**Success = Farmers get trustworthy daily task lists based on weather, soil, and crop data.**

---

This document serves as the formal **Technical Manifesto** and **Architectural Blueprint** for the Yonca AI Prototype. It outlines our strategic choices, design standards, and the "Logic-First" methodology required to deliver a high-accuracy, integratable AI engine for Digital Umbrella.

---

## 1. Executive Standpoint: The "Sidecar" Strategy

Our primary architectural decision is the **Sidecar Intelligence Model**. Instead of proposing a rebuild of the Yonca platform, we position our prototype as a detached, high-performance module.

* **Integration Philosophy:** The AI engine communicates exclusively via a **Headless API Layer (REST/GraphQL)**. This ensures that Digital Umbrella’s core GovTech and subsidy systems remain untouched and secure.
* **Data Sovereignty:** By utilizing **100% Synthetic Datasets**, we remove all legal and operational friction. The system is built to ingest "Real World" data hooks in the future without changing the underlying logic.
* **Edge-Ready Logic:** We prioritize **Lightweight Inference**. Our choice of **Qwen2.5-7B (Quantized)** ensures that the engine can run on local farm servers or in low-connectivity zones, fulfilling the "Data Safety" and "Low Connectivity" requirements.

---

## 2. Architectural Blueprint (IT Standards)

To ensure the prototype is "Production-Ready," we adhere to the following technical stack and data flow:

| Layer | Standard / Tool | Purpose |
| --- | --- | --- |
| **Inference Engine** | Qwen2.5-7B (GGUF) | Multilingual logic & local execution. |
| **Logic Layer** | Deterministic Agronomy Rulebook | Overrides LLM "hallucinations" with hard rules. |
| **API Framework** | FastAPI (Swagger/OpenAPI) | Provides the integratable backend documentation. |
| **UI Framework** | Mobile-Framed Streamlit | High-speed logic validation with a mobile "look." |
| **Data Engine** | Synthetic Scenario Manager | Generates 5 distinct farm profiles (Wheat, Livestock, etc.). |

### Data Flow Diagram (Conceptual)

`Farmer Input (AZ)` → `Intent Matcher` → `Synthetic Profile Lookup` → `Agronomy Logic Check` → `LLM Response Generation` → `JSON Payload` → `Mobile UI Card`

---

## 3. UI/UX Declaration of Standards

The UI is designed to be **Invisible yet Informative**. We follow the "Contextual Card" pattern used in modern high-end mobile ecosystems.

* **Visual Continuity:** We utilize the **Yonca Palette** (Forest Green `#2E7D32`) and rounded-corner surfaces (15px) to match their existing brand identity.
* **The "Why" Factor:** Every AI recommendation includes a **Source Citation** (e.g., *Rule: Early Frost Protection v1.2*). Farmers trust logic they can verify.
* **Native-First Viewport:** Even within a web-based demo (Streamlit), we force a **Mobile Aspect Ratio** to prevent "Desktop Drift" and show immediate compatibility with their smartphone app.

---

## 4. Codebase Architecture (Current State)

The codebase follows a **clean sidecar architecture**:

```
src/yonca/
├── sidecar/              # 🎯 CORE: Headless Intelligence Engine
│   ├── rules_registry    # Single source of truth: agronomy rules (AZ- prefixes)
│   ├── intent_matcher    # Azerbaijani intent detection (unified patterns)
│   ├── recommendation_service  # Main orchestrator
│   ├── schedule_service  # Daily task generation
│   ├── pii_gateway       # Zero-trust data sanitization
│   ├── rag_engine        # Rule validation + LLM
│   ├── lite_inference    # Edge/offline inference modes
│   ├── trust             # Confidence scoring with citations
│   └── digital_twin      # Simulation engine
├── api/                  # REST + GraphQL endpoints
├── agent/                # LangGraph tools (optional advanced mode)
├── data/                 # Synthetic scenarios + generators
├── models/               # Canonical Pydantic models
└── umbrella/             # Streamlit demo UI
```

**Key Principle:** Everything flows through `sidecar/` — the UI and API are thin consumers.

---

## 5. Success Metric Validation

Our standpoint ensures we hit all the challenge's "Success Indicators":

1. **Logical Accuracy (≥ 90%)**: Achieved via the `AgronomyGuard` rule-base.
2. **100% Data Safety**: Guaranteed by the `ScenarioEngine` synthetic isolation.
3. **UX Compatibility**: Demonstrated by the Mobile-First CSS Injection.