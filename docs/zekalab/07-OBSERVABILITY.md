# 📊 ALEM Observability Guide

> **Purpose:** Logging, tracing, and monitoring for ALEM production visibility.

---

## ✅ Implementation Status

| Component | Status | Location |
|:----------|:-------|:---------|
| **Langfuse Integration** | ✅ Implemented | `src/yonca/observability/langfuse.py` |
| Docker Compose | ✅ Configured | `docker-compose.local.yml` |
| Agent Callbacks | ✅ Wired | `src/yonca/agent/graph.py` |
| Prometheus Metrics | ⏳ Not implemented | Future |

---

## 🔍 Langfuse: Self-Hosted LLM Observability

**Langfuse** provides 100% data residency — all traces stay within your infrastructure.

### Quick Start

```bash
# 1. Start Langfuse
docker-compose -f docker-compose.local.yml up langfuse-server langfuse-db -d

# 2. Open http://localhost:3001, create account, get API keys

# 3. Add to .env:
YONCA_LANGFUSE_SECRET_KEY=sk-lf-...
YONCA_LANGFUSE_PUBLIC_KEY=pk-lf-...
YONCA_LANGFUSE_HOST=http://localhost:3001
```

### Dashboard Features

- 🔍 Full LangGraph node tracing with timing
- 💰 Token/cost tracking per model
- 📊 Session grouping by thread_id
- 👥 Per-user analytics
- 📝 Prompt versioning
- ⚡ Evaluation datasets

### Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart LR
    subgraph app["🧠 ALEM Agent"]
        graph["LangGraph"]
        llm["LLM Provider"]
    end

    subgraph observe["📊 Langfuse (:3001)"]
        traces["Traces"]
        sessions["Sessions"]
        costs["Cost Tracking"]
    end

    graph --> |"Callbacks"| traces
    llm --> |"Token usage"| costs

    style observe fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

---

## 📈 Metric Categories

| Category | Examples | Status |
|:---------|:---------|:-------|
| **LLM Metrics** | Token usage, latency, costs | ✅ Langfuse |
| **Session Metrics** | Thread count, user activity | ✅ Langfuse |
| **System Metrics** | CPU, memory, GPU | ⏳ Prometheus (future) |
| **Business Metrics** | Task completion, satisfaction | ⏳ Custom (future) |

---

## 🔧 Configuration

```python
# src/yonca/config.py
class Settings:
    langfuse_enabled: bool = True
    langfuse_host: str = "http://localhost:3001"
    langfuse_secret_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_sample_rate: float = 1.0
    langfuse_debug: bool = False
```

---

## 📋 Future: Prometheus/Grafana

Optional infrastructure monitoring (lower priority than Langfuse):

| Metric | Type | Use |
|:-------|:-----|:----|
| `alem_requests_total` | Counter | Request rate |
| `alem_request_duration_seconds` | Histogram | Latency |
| `alem_active_sessions` | Gauge | Concurrent users |
| `alem_errors_total` | Counter | Error tracking |
