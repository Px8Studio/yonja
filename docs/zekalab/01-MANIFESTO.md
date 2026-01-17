# 🎯 Yonca AI — Technical Manifesto

> **The North Star:** Build a **Headless AI Sidecar** that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 🌟 Ultimate Goal

**Create a production-ready AI farm planning assistant** that:

```mermaid
mindmap
  root((🌿 Yonca AI))
    🔌 Offline-First
      Edge devices
      Farmer phones
      Local servers
    🗣️ Native Azerbaijani
      Dialect support
      Cultural context
    ✅ Logic-First
      Deterministic rules
      ≥90% accuracy
      No hallucinations
    🔒 Data Safe
      PII gateway
      Zero real data
      Synthetic only
    🧩 Plug & Play
      REST/GraphQL
      No EKTIS changes
      Modular design
```

**Success = Farmers get trustworthy daily task lists based on weather, soil, and crop data.**

---

## 1. The "Sidecar" Strategy

Our primary architectural decision is the **Sidecar Intelligence Model**. Instead of proposing a rebuild of the Yonca platform, we position our prototype as a detached, high-performance module that sits alongside the existing system.

### Strategy Pillars

| Pillar | Implementation | Benefit |
|:-------|:---------------|:--------|
| **🔗 Integration Philosophy** | Headless API Layer (REST/GraphQL) | Core GovTech systems remain untouched |
| **🔒 Data Sovereignty** | Mirror-Image Synthetic Engine | Zero legal/operational friction |
| **📶 Edge-Ready Logic** | Qwen2.5-7B Quantized (GGUF) | Works offline in rural zones |
| **🔄 Hot-Swap Ready** | Schema-synchronized data layer | Flip from synthetic to real with zero code changes |

### Four Guarantees

| # | Guarantee | How We Deliver |
|:-:|:----------|:---------------|
| 1 | **Never touches EKTIS database** | Uses schema-synchronized synthetic scenarios only |
| 2 | **Strips all PII** | Farmer names/IDs hashed before AI processing |
| 3 | **Validates with rules** | Every LLM output checked against agronomy rulebook |
| 4 | **Ready to plug in** | Same API contract—just flip data source later |

---

## 2. UI/UX Design System

The AI Assistant integrates as a **new navigation tab** positioned between "Məntəqələr" (Places) and "Təsərrüfatlarım" (My Farms) in the bottom navigation bar.

### Navigation Placement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        📱 Bottom Navigation Bar                              │
├─────────────┬─────────────┬─────────────┬─────────────────┬─────────────────┤
│     🏠      │     📍      │    🤖       │       🌾        │        ⋯        │
│ Əsas səhifə │  Məntəqələr │ AI Köməkçi  │  Təsərrüfatlarım│    Daha çox     │
└─────────────┴─────────────┴──────┬──────┴─────────────────┴─────────────────┘
                                   │
                             ▲ NEW TAB ▲
                         (Primary: #2E7D32)
```

### Design Principles (Extracted from Yonca App)

| Principle | Implementation | Reference |
|:----------|:---------------|:----------|
| **🎨 Brand Palette** | Primary `#2E7D32`, Accent `#4CAF50`, Background `#F5F5F5` | Logo, buttons, cards |
| **📐 Card System** | 12-16px radius, subtle shadow, white background | Feature cards, weather widget |
| **📝 Typography** | Bold headers, regular body, Azerbaijani-optimized | Clear hierarchy |
| **📏 Spacing** | 16px grid, 12px card gaps, 20px section margins | Consistent rhythm |
| **🌡️ Context Cards** | Location + weather always visible | Top of home screen |
| **✅ Trust Signals** | Source citations, confidence indicators | Every AI recommendation |

### AI Assistant Tab Behavior

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
flowchart LR
    subgraph data["🔄 Auto-Loaded Context"]
        direction TB
        user["👤 User Profile"]
        farms2["🌾 All User Farms"]
        weather["🌤️ Local Weather"]
        ndvi["📡 Latest NDVI"]
    end
    
    subgraph tab["🤖 AI Köməkçi Tab"]
        direction TB
        context["📋 Context Header<br/><i>User + Active Farms Summary</i>"]
        chat["💬 Chat Interface<br/><i>Conversation with AI</i>"]
        quick["⚡ Quick Actions<br/><i>Common Tasks</i>"]
        
        context --> chat --> quick
    end
    
    data --> tab
    
    style tab fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    style context fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style data fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
```

---

## 3. Success Metrics

| Metric | Target | Achieved By |
|:-------|:-------|:------------|
| **Logical Accuracy** | ≥ 90% | Agronomy rulebook validation layer |
| **Data Safety** | 100% | Mirror-image synthetic engine + PII gateway |
| **Integration Debt** | Zero | Schema-synchronized API contract |
| **Handoff Friction** | Minimal | Dockerized microservice delivery |

---

<div align="center">

**📄 Document:** `01-MANIFESTO.md`  
**🔄 Next:** [02-SYNTHETIC-DATA-ENGINE.md](02-SYNTHETIC-DATA-ENGINE.md) — Mirror-Image Data Strategy

</div>
