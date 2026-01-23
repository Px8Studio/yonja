# 🌿 ALEM Technical Documentation

> **ALEM** = **A**gronomical **L**ogic & **E**valuation **M**odel
> Azerbaijani agricultural AI with 100% open-source models and full data sovereignty.

---

## 🎯 Quick Overview

```mermaid
%%{init: {'theme': 'neutral'}}%%
mindmap
  root((🌿 ALEM))
    🗣️ Azerbaijani-First
      Native language
      Local crops
    ✅ Rule-Validated
      90%+ accuracy target
      No hallucinations
    🔒 Data Sovereignty
      Synthetic profiles
      Self-hostable
    🌿 Open-Source
      Llama/Qwen models
      No vendor lock-in
```

**Key Features:**
- ✅ Llama 4 Maverick, Llama 3.3 70B, Qwen 3 32B (Apache 2.0 / Llama Community License)
- ✅ Deploy in Azerbaijan (self-hosted or AzInTelecom Cloud)
- ✅ 200-300 tok/s performance
- ✅ Chainlit demo UI with LangGraph

---

## 📚 Documentation Index

### Core

| Doc | Purpose |
|:----|:--------|
| [00-VISUAL-STYLE-GUIDE](00-VISUAL-STYLE-GUIDE.md) | Mermaid diagram standards |
| [01-MANIFESTO](01-MANIFESTO.md) | Vision, strategy, success metrics |
| [02-SYNTHETIC-DATA-ENGINE](02-SYNTHETIC-DATA-ENGINE.md) | Schema design, mirror-image data |
| [03-ARCHITECTURE](03-ARCHITECTURE.md) | Components, data flow, operations |

### AI & Prompting

| Doc | Purpose |
|:----|:--------|
| [04-TESTING-STRATEGY](04-TESTING-STRATEGY.md) | Evaluation framework, golden dataset |
| [05-PROMPT-CONVERSATION](05-PROMPT-CONVERSATION.md) | System prompts, intent taxonomy |

### Operations & Infrastructure

| Doc | Purpose |
|:----|:--------|
| [LANGGRAPH_ARCHITECTURE_GUIDE](LANGGRAPH_ARCHITECTURE_GUIDE.md) | **⭐ START HERE:** Dev vs Production, component relationships, multi-channel design, production stack |
| [LANGGRAPH_TESTING_GUIDE](LANGGRAPH_TESTING_GUIDE.md) | Testing LangGraph execution and graph client |
| [LANGGRAPH_DOCKER_DEPLOYMENT](LANGGRAPH_DOCKER_DEPLOYMENT.md) | Docker Compose setup and containerization |
| [MCP-BLUEPRINT](MCP-BLUEPRINT.md) | Sovereign AI stack (LangGraph + FastMCP + Chainlit) and developer prompt |
| [07-OBSERVABILITY](07-OBSERVABILITY.md) | Langfuse tracing, metrics |
| [08-SECURITY](08-SECURITY.md) | Input validation, PII protection |
| [09-PERFORMANCE-SLA](09-PERFORMANCE-SLA.md) | Latency targets, SLOs |
| [17-SECURITY-ENHANCEMENT-PLAN](17-SECURITY-ENHANCEMENT-PLAN.md) | 🔐 **Production security roadmap** |
| [22-QUALITY-GATE-SYSTEM](22-QUALITY-GATE-SYSTEM.md) | 🛡️ **Pre-commit hooks & quality checks** |

### UI & Frontend

| Doc | Purpose |
|:----|:--------|
| [CHAT_UI_MODEL_AND_INTERACTION](CHAT_UI_MODEL_AND_INTERACTION.md) | 🎯 **Model selection (header) & interaction mode (sidebar) architecture** |
| [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | Demo UI implementation |

### Deployment

| Doc | Purpose |
|:----|:--------|
| [12-DEPLOYMENT-PRICING](12-DEPLOYMENT-PRICING.md) | DigiRella options, costs, ALEM versioning |
| [14-DISCOVERY-QUESTIONS](14-DISCOVERY-QUESTIONS.md) | Integration questions for Digital Umbrella |
| [15-IMPLEMENTATION-BACKLOG](15-IMPLEMENTATION-BACKLOG.md) | 📋 Unimplemented features tracker |
| [16-ADVANCED-FEATURES](16-ADVANCED-FEATURES.md) | 🎨 Multimodal, NL-to-SQL, Vision-to-Action |
| [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) | 🌐 **Partnership strategy & phased roadmap** |
| [19-YONCA-AI-INTEGRATION-UNIVERSE](19-YONCA-AI-INTEGRATION-UNIVERSE.md) | 🌌 **Complete integration landscape & data flows** |
| [20-INTEGRATION-API](20-INTEGRATION-API.md) | 🔌 **API contract for Yonca Mobile integration** |

---

## 🗺️ Finding What You Need

**Start here:** [QUICK_NAVIGATION.md](QUICK_NAVIGATION.md) — Find docs by your question or role

---

## 🧹 Documentation Maintenance

**Recently Consolidated:** [DOCUMENTATION_CONSOLIDATION_SUMMARY.md](DOCUMENTATION_CONSOLIDATION_SUMMARY.md)
- Merged 5 redundant LangGraph docs into 1 master guide
- Added UI clarity documentation
- Removed stale/theoretical recommendations
- Updated all references

---

## 🚀 Quick Start

```powershell
# 1. Start infrastructure
docker-compose -f docker-compose.local.yml up -d

# 2. Run migrations
$env:DATABASE_URL = "postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca"
alembic upgrade head

# 3. Start demo UI
cd demo-ui && chainlit run app.py -w --port 8501
```

**Service URLs:**
- Chainlit UI: http://localhost:8501
- Langfuse: http://localhost:3001
- PostgreSQL: localhost:5433
- Redis: localhost:6379

---

## 🏗️ Architecture Summary

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TB
    subgraph external["🌐 External: Yonca Mobile (Digital Umbrella)"]
        yonca_mobile["📱 Production App<br/><i>Future data source</i>"]
    end

    subgraph yonca_ai["🤖 YONCA AI (Our System)"]
        subgraph ui["🖥️ Demo UI"]
            chainlit["Chainlit :8501"]
        end

        subgraph brain["🧠 ALEM Agent"]
            agent["LangGraph"]
            llm["Groq/Ollama"]
        end

        subgraph data["💾 App Data (Docker)"]
            pg["🐘 PostgreSQL :5433"]
            redis["🔴 Redis :6379"]
        end
    end

    subgraph observe["📊 Langfuse Stack (Separate)"]
        langfuse_db["🐘 PostgreSQL<br/><i>auto-managed</i>"]
        langfuse_ui["Langfuse :3001"]
    end

    yonca_mobile -.->|"future sync"| pg
    chainlit --> agent --> llm
    agent --> pg
    agent --> redis
    agent -.->|traces| langfuse_db
    langfuse_db --> langfuse_ui

    style external fill:#fff3e0,stroke:#f57c00,stroke-dasharray: 5 5
    style yonca_ai fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style observe fill:#f3e5f5,stroke:#7b1fa2
```

> **Key:** Yonca AI = our system | Yonca Mobile = Digital Umbrella's production app
> See [03-ARCHITECTURE](03-ARCHITECTURE.md) for full data ecosystem + VS Code DB access.
