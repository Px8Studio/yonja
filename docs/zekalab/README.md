# 🌿 ALEM Technical Documentation

> **ALEM** = **A**gronomical **L**ogic & **E**valuation **M**odel
> Azerbaijani agricultural AI with 100% open-source models and full data sovereignty.

---

## 🎯 Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ALEM SOVEREIGN AI STACK                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   CHAINLIT ────────▶ LANGGRAPH ────────▶ MCP SERVERS                    │
│   (Window)           (Brain)             (Tools/Data)                   │
│                                                                         │
│   Shows UI ◀──────── Orchestrates ──────▶ Weather (real data)           │
│   Streams tokens      nodes               ZekaLab (rules)               │
│   Handles OAuth       Manages state       Postgres (DB access)          │
│                       Calls MCP tools                                   │
│                                                                         │
│   ───────────────────────────────────────────────────────────────       │
│                                                                         │
│   🔄 LangGraph is BIDIRECTIONAL:                                        │
│      • As CLIENT → Calls external MCP tools                             │
│      • As SERVER → Exposes ALEM as an MCP tool to other systems         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- ✅ Llama 4, Qwen 3 (Apache 2.0 / Open Source)
- ✅ Deploy in Azerbaijan (self-hosted or cloud)
- ✅ MCP-native tool orchestration
- ✅ Chainlit UI + LangGraph agent

---

## 📚 Documentation (Start Here)

### 🔌 MCP Integration
| Doc | Purpose |
|:----|:--------|
| **[MCP-ARCHITECTURE](MCP-ARCHITECTURE.md)** | ⭐ **Single source of truth** — Status, relationships, what's next |
| [MCP-BLUEPRINT](MCP-BLUEPRINT.md) | Developer prompt for new sessions |

### 🏗️ Architecture
| Doc | Purpose |
|:----|:--------|
| [03-ARCHITECTURE](03-ARCHITECTURE.md) | Full system architecture |
| [01-MANIFESTO](01-MANIFESTO.md) | Vision & success metrics |

### 🔐 Quality & Security
| Doc | Purpose |
|:----|:--------|
| [22-QUALITY-GATE-SYSTEM](22-QUALITY-GATE-SYSTEM.md) | Pre-commit hooks, linting |
| [08-SECURITY](08-SECURITY.md) | Input validation, PII |

### 🚀 Operations
| Doc | Purpose |
|:----|:--------|
| [PHASE-3-DEPLOYMENT-GUIDE](PHASE-3-DEPLOYMENT-GUIDE.md) | MCP server deployment |
| [12-DEPLOYMENT-PRICING](12-DEPLOYMENT-PRICING.md) | Hosting options |

### 🔮 Roadmap
| Doc | Purpose |
|:----|:--------|
| [00-IMPLEMENTATION-BACKLOG](00-IMPLEMENTATION-BACKLOG.md) | What's next |
| [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) | Partner integrations |

---

## 🗂️ Full Index

See [DOCUMENTATION-INDEX.md](DOCUMENTATION-INDEX.md) for complete categorized list with status.
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
