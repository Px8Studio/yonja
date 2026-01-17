# 🌿 Yonca AI Sidecar — Technical Documentation

> **Mission:** Build a Headless AI Sidecar that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 📚 Documentation Index

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 1 | **[01-MANIFESTO.md](01-MANIFESTO.md)** | Vision, strategy, success metrics | Starting the project |
| 2 | **[02-SYNTHETIC-DATA-ENGINE.md](02-SYNTHETIC-DATA-ENGINE.md)** | Schema design, synthetic profiles, data contracts | Building data layer |
| 3 | **[03-ARCHITECTURE.md](03-ARCHITECTURE.md)** | **Complete technical reference:** Auth, APIs, Docker, LangGraph, Roadmap | Building & deploying |

---

## 🎯 Core Principles

| Principle | Implementation |
|:----------|:---------------|
| 🔒 **Zero Real Data** | Mirror-image synthetic engine replicating EKTIS schema |
| ✅ **Rule-Validated** | Agronomy rulebook overrides LLM (≥90% accuracy) |
| 📶 **Offline-First** | Qwen2.5 GGUF quantized for rural Azerbaijan |
| 🔌 **Plug-and-Play** | Single REST endpoint, Dockerized microservice |
| 🔄 **Hot-Swap Ready** | Flip from synthetic to real data with zero code changes |
| 🔐 **Auth Bridge** | Leverages existing mygov ID/SİMA/Asan İmza tokens |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    🐳 DOCKER CONTAINER                       │
├─────────────────────────────────────────────────────────────┤
│  🔌 FastAPI Gateway  →  🧠 LangGraph Brain  →  🤖 Qwen2.5   │
│         ↓                      ↓                            │
│  🔐 JWT Validation      ⚡ Redis (Memory)                   │
│                               ↓                             │
│                    🐘 PostgreSQL (Synthetic Data)           │
└─────────────────────────────────────────────────────────────┘
         ↑                                    
    📱 Yonca App (mygov ID Token)            
```

---

## 🚀 Quick Start

```bash
# Read the docs in order
cat docs/zekalab/01-MANIFESTO.md           # Vision (5 min)
cat docs/zekalab/02-SYNTHETIC-DATA-ENGINE.md  # Data Strategy (10 min)
cat docs/zekalab/03-ARCHITECTURE.md        # Technical Deep-Dive (20 min)
```

---

## 📊 Project Status

| Phase | Status | Timeline | Key Deliverables |
|:------|:-------|:---------|:-----------------|
| **Phase 1: Prototype** | 🟢 Active | Now - 6 months | Synthetic data, Docker image, LangGraph |
| **Phase 2: Hybrid** | ⏳ Planned | 6-12 months | Real weather APIs, k-anonymity |
| **Phase 3: Production** | 📋 Roadmap | 12-24 months | EKTIS integration, OAuth 2.0 |

---

<div align="center">

**Built by ZekaLab** 🧪  
*"Logic-first AI for Azerbaijani Agriculture"*

</div>
