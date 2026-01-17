# 🌿 Yonca AI Sidecar — Technical Documentation Hub

> **Mission:** Build a Headless AI Sidecar that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 📚 Documentation Map

```mermaid
flowchart TB
    subgraph docs["📁 /docs/zekalab"]
        README["📋 README.md<br/><i>You are here</i>"]
        
        subgraph strategic["🎯 Strategic Layer"]
            MANIFESTO["01-MANIFESTO.md<br/><b>Vision & Principles</b><br/>North star, success metrics"]
        end
        
        subgraph planning["📊 Planning Layer"]
            DATAPLAN["02-GAP-ANALYSIS.md<br/><b>Client Discovery</b><br/>Data gaps, questions, schemas"]
        end
        
        subgraph technical["⚙️ Technical Layer"]
            ARCHITECTURE["03-ARCHITECTURE.md<br/><b>Implementation Deep-Dive</b><br/>Components, roadmap, accuracy"]
        end
        
        README --> MANIFESTO
        README --> DATAPLAN
        README --> ARCHITECTURE
        MANIFESTO -.->|"informs"| DATAPLAN
        DATAPLAN -.->|"feeds into"| ARCHITECTURE
    end
    
    style README fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style MANIFESTO fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style DATAPLAN fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style ARCHITECTURE fill:#fce4ec,stroke:#c62828,stroke-width:2px
```

---

## 🗂️ Document Purposes

| # | Document | Purpose | Audience | Read When... |
|:-:|:---------|:--------|:---------|:-------------|
| 1 | **[01-MANIFESTO.md](01-MANIFESTO.md)** | Vision, goals, success metrics | Everyone | Starting the project |
| 2 | **[02-GAP-ANALYSIS.md](02-GAP-ANALYSIS.md)** | Client questions, data gaps, schemas | Product/Client | Planning integration |
| 3 | **[03-ARCHITECTURE.md](03-ARCHITECTURE.md)** | Technical deep-dive, components, roadmap | Engineers | Building features |

---

## 🎯 The Sidecar Concept (At a Glance)

```mermaid
graph LR
    subgraph existing["🏛️ YONCA PLATFORM<br/><i>(Legal/Financial - Untouched)</i>"]
        APP[📱 Mobile App]
        EKTIS[(🗄️ EKTIS DB)]
        APP <--> EKTIS
    end
    
    subgraph sidecar["🧠 AI SIDECAR<br/><i>(This Repository)</i>"]
        API[🔌 Headless API]
        BRAIN[🤖 LLM + Rules]
        DATA[🧪 Synthetic Data]
        API --> BRAIN
        BRAIN --> DATA
    end
    
    APP -->|"Anonymized Request"| API
    API -->|"Verified Advice"| APP
    
    style existing fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style sidecar fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
```

### Core Principles

| Principle | Implementation | Why It Matters |
|:----------|:---------------|:---------------|
| 🔒 **Zero Real Data** | 100% synthetic scenarios | Legal safety, no PII risk |
| ✅ **Rule-Validated** | Agronomy rulebook overrides LLM | ≥90% accuracy guarantee |
| 📶 **Offline-First** | Qwen2.5 GGUF quantized | Works in rural Azerbaijan |
| 🔌 **Plug-and-Play** | REST/GraphQL API contract | Easy Digital Umbrella integration |

---

## 🚀 Quick Start

```bash
# 1. Read the manifesto (5 min)
cat docs/zekalab/01-MANIFESTO.md

# 2. Understand the gaps (10 min)  
cat docs/zekalab/02-GAP-ANALYSIS.md

# 3. Deep-dive architecture (20 min)
cat docs/zekalab/03-ARCHITECTURE.md
```

---

## 📊 Project Status

```mermaid
gantt
    title Yonca AI Sidecar Roadmap
    dateFormat  YYYY-MM
    
    section Phase 1: Prototype
    Synthetic Data Engine     :done,    p1a, 2025-07, 2025-10
    Rule-based Recommendations:done,    p1b, 2025-08, 2025-11
    LLM Integration (Qwen2.5) :active,  p1c, 2025-10, 2026-01
    API Contract Definition   :         p1d, 2025-12, 2026-02
    
    section Phase 2: Hybrid
    Real Weather Integration  :         p2a, 2026-03, 2026-06
    Anonymized Farm Blending  :         p2b, 2026-05, 2026-09
    
    section Phase 3: Production
    ASAN Kənd Integration     :         p3a, 2026-10, 2027-02
    Federated Learning        :         p3b, 2027-01, 2027-06
```

---

## 🔗 Related Documents

- [/docs/yonca/](../yonca/) — Client-facing Yonca platform documentation
- [/src/yonca/sidecar/](../../src/yonca/sidecar/) — Core sidecar implementation

---

<div align="center">

**Built by ZekaLab** 🧪

*"Logic-first AI for Azerbaijani Agriculture"*

</div>
