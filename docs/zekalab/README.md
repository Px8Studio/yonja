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

### Operations

| Doc | Purpose |
|:----|:--------|
| [07-OBSERVABILITY](07-OBSERVABILITY.md) | Langfuse tracing, metrics |
| [08-SECURITY](08-SECURITY.md) | Input validation, PII protection |
| [09-PERFORMANCE-SLA](09-PERFORMANCE-SLA.md) | Latency targets, SLOs |

### Deployment

| Doc | Purpose |
|:----|:--------|
| [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | Demo UI implementation |
| [12-DEPLOYMENT-PRICING](12-DEPLOYMENT-PRICING.md) | DigiRella options, costs |
| [14-DISCOVERY-QUESTIONS](14-DISCOVERY-QUESTIONS.md) | Integration questions for Digital Umbrella |

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
flowchart LR
    subgraph ui["🖥️ UI"]
        chainlit["Chainlit :8501"]
    end
    
    subgraph brain["🧠 Agent"]
        langgraph["LangGraph"]
        llm["Groq/Ollama"]
    end
    
    subgraph data["💾 Data"]
        pg["PostgreSQL :5433"]
        redis["Redis :6379"]
    end
    
    subgraph observe["📊 Observability"]
        langfuse["Langfuse :3001"]
    end
    
    chainlit --> langgraph --> llm
    langgraph --> pg
    langgraph --> redis
    langgraph --> langfuse
```

> See [03-ARCHITECTURE](03-ARCHITECTURE.md) for full details.
