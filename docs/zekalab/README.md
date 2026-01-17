# 🌿 Yonca AI Sidecar — Technical Documentation

> **Mission:** Build a Headless AI Sidecar that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 📚 Documentation Index

### Core Documentation

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 1 | **[01-MANIFESTO.md](01-MANIFESTO.md)** | Vision, strategy, success metrics | Starting the project |
| 2 | **[02-SYNTHETIC-DATA-ENGINE.md](02-SYNTHETIC-DATA-ENGINE.md)** | Schema design, synthetic profiles, data contracts | Building data layer |
| 3 | **[03-ARCHITECTURE.md](03-ARCHITECTURE.md)** | **Complete technical reference:** Auth, APIs, Docker, LangGraph, Roadmap | Building & deploying |

### AI & Quality Assurance

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 4 | **[04-TESTING-STRATEGY.md](04-TESTING-STRATEGY.md)** | Evaluation framework, golden datasets, accuracy benchmarks | Setting up testing |
| 5 | **[05-PROMPT-ENGINEERING.md](05-PROMPT-ENGINEERING.md)** | System prompts, versioning, few-shot examples | Tuning LLM behavior |
| 6 | **[06-CONVERSATION-DESIGN.md](06-CONVERSATION-DESIGN.md)** | Dialogue flows, intent taxonomy, edge cases | Designing UX |

### Operations & Infrastructure

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 7 | **[07-OBSERVABILITY.md](07-OBSERVABILITY.md)** | Metrics, logging, tracing, alerting | Setting up monitoring |
| 8 | **[08-SECURITY-HARDENING.md](08-SECURITY-HARDENING.md)** | Input validation, prompt injection defense, auth | Securing the system |
| 9 | **[09-PERFORMANCE-SLA.md](09-PERFORMANCE-SLA.md)** | Latency targets, scaling strategy, load testing | Optimizing performance |
| 10 | **[10-DEVOPS-RUNBOOK.md](10-DEVOPS-RUNBOOK.md)** | CI/CD, deployment, rollback, disaster recovery | Deploying & operating |

### Demo & Presentation

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 11 | **[11-DEMO-UI-SPEC.md](11-DEMO-UI-SPEC.md)** | Chainlit setup, demo scenarios, Azerbaijani theme | Building the demo |

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
