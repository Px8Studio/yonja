# 🌿 Yonca AI Sidecar — Technical Documentation

> **Mission:** Build a Headless AI Sidecar that delivers personalized, rule-validated farm recommendations to Azerbaijani farmers—without ever touching real data.

---

## 🌿 Open-Source First Architecture

**Yonca AI is built on open-source models** to demonstrate enterprise-ready AI that:

✅ **Can be self-hosted** - Full control over deployment  
✅ **No vendor lock-in** - Not dependent on proprietary APIs  
✅ **Transparent & auditable** - Open weights, open architectures  
✅ **Production-ready** - Enterprise performance (200-300 tok/s)  

### Deployment Modes

| Mode | Models | License | Self-Host | Best For |
|:-----|:-------|:--------|:----------|:---------|
| 🌿 **Open-Source** | Llama 3.3, Qwen 3 | Apache 2.0 / Llama Community | ✅ Yes | **Recommended** |
| ☁️ **Proprietary** | Gemini | Proprietary | ❌ No | Fallback only |

See **[12-DUAL-MODE-DEPLOYMENT.md](12-DUAL-MODE-DEPLOYMENT.md)** for full details.

---

## 📚 Documentation Index

### Core Documentation

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 1 | **[01-MANIFESTO.md](01-MANIFESTO.md)** | Vision, strategy, success metrics | Starting the project |
| 2 | **[02-SYNTHETIC-DATA-ENGINE.md](02-SYNTHETIC-DATA-ENGINE.md)** | Schema design, synthetic profiles, data contracts | Building data layer |
| 3 | **[03-ARCHITECTURE.md](03-ARCHITECTURE.md)** | Core architecture: Auth, LangGraph, data flow, roadmap | Understanding the system |

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
| 8 | **[08-SECURITY-HARDENING.md](08-SECURITY-HARDENING.md)** | Input validation, prompt injection defense, PII protection | Securing the system |
| 9 | **[09-PERFORMANCE-SLA.md](09-PERFORMANCE-SLA.md)** | Latency targets, scaling strategy, load testing | Optimizing performance |
| 10 | **[10-DEVOPS-RUNBOOK.md](10-DEVOPS-RUNBOOK.md)** | CI/CD, Docker, deployment, environment configs | Deploying & operating |

### Demo & Presentation

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 11 | **[11-DEMO-UI-SPEC.md](11-DEMO-UI-SPEC.md)** | Chainlit + LangGraph native integration, demo scenarios | Building the demo |

> 💡 **Demo Stack:** We use Chainlit's **native LangGraph integration** (`cl.LangchainCallbackHandler`) for automatic step visualization, token streaming, and session persistence. This reduces UI development from **1-2 weeks** (custom React) to **~1 hour**.

### Deployment & Implementation

| # | Document | Purpose | Read When... |
|:-:|:---------|:--------|:-------------|
| 12 | **[12-DUAL-MODE-DEPLOYMENT.md](12-DUAL-MODE-DEPLOYMENT.md)** | Local vs Cloud, LLM abstraction, Docker configs | Setting up deployment |
| 13 | **[13-IMPLEMENTATION-PLAN.md](13-IMPLEMENTATION-PLAN.md)** | Step-by-step build guide, milestones, checklist | Starting implementation |

---

## 📋 Document Cross-References

To avoid duplication, content is organized as follows:

| Topic | Primary Document | References |
|:------|:-----------------|:-----------|
| **Schemas & Data Models** | 02-SYNTHETIC-DATA-ENGINE | 03-ARCHITECTURE links here |
| **Security & PII** | 08-SECURITY-HARDENING | 03-ARCHITECTURE summarizes |
| **Deployment & Docker** | 10-DEVOPS-RUNBOOK | 03-ARCHITECTURE links here |
| **Prompts & Dialogue** | 05-PROMPT + 06-CONVERSATION | 04-TESTING uses examples |
| **Metrics & Monitoring** | 07-OBSERVABILITY | 09-PERFORMANCE references |

---

## 🎯 Core Principles

| Principle | Implementation |
|:----------|:---------------|
| 🔒 **Zero Real Data** | Mirror-image synthetic engine replicating EKTIS schema |
| ✅ **Rule-Validated** | Agronomy rulebook overrides LLM (≥90% accuracy) |
| 🌿 **Open-Source First** | Llama + Qwen models that can be self-hosted |
| 🔌 **Plug-and-Play** | Single REST endpoint, Dockerized microservice |
| 🔄 **Hot-Swap Ready** | Flip from synthetic to real data with zero code changes |
| 🔐 **Auth Bridge** | Leverages existing mygov ID/SİMA/Asan İmza tokens |

---

## 🏗️ Architecture Overview

### Open-Source Mode (Groq or Self-Hosted)
```
┌─────────────────────────────────────────────────────────────┐
│                 🌿 OPEN-SOURCE MODE                         │
├─────────────────────────────────────────────────────────────┤
│  🔌 FastAPI Gateway  →  🧠 LangGraph Brain  →  ⚡ Groq API   │
│         ↓                      ↓              (Llama/Qwen)  │
│  🔐 JWT Validation      ⚡ Redis (Memory)       OR          │
│                               ↓              🏢 Self-Hosted  │
│                    🐘 PostgreSQL (Synthetic Data)           │
└─────────────────────────────────────────────────────────────┘
```

### Proprietary Fallback (Render.com + Gemini API)
```
┌─────────────────────────────────────────────────────────────┐
│                   ☁️ PROPRIETARY MODE (⚠️ Fallback)          │
├─────────────────────────────────────────────────────────────┤
│  🔌 FastAPI Gateway  →  🧠 LangGraph Brain  →  🔮 Gemini    │
│         ↓                      ↓                 (API)      │
│  🔐 JWT Validation      ⚡ Redis (Managed)     ❌ Can't      │
│                               ↓                 Self-Host   │
│                    🐘 PostgreSQL (Managed)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Read the docs in order
cat docs/zekalab/01-MANIFESTO.md              # Vision (5 min)
cat docs/zekalab/12-DUAL-MODE-DEPLOYMENT.md   # Deployment Strategy (10 min)
cat docs/zekalab/13-IMPLEMENTATION-PLAN.md    # Build Guide (15 min)

# 2. Open-Source Development (Recommended)
export YONCA_GROQ_API_KEY=gsk_your_key_here
docker-compose -f docker-compose.local.yml up -d

# 3. Self-Hosted Production (Government Compliance)
# Deploy vLLM/TGI on your infrastructure
# Point YONCA_GROQ_BASE_URL to your cluster
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
