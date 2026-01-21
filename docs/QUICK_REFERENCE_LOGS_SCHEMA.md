# 🚀 Quick Reference — Logs & Schema

> **Quick answers to:** How to view logs? What can I change in the database?

---

## 📊 Viewing Logs

### Individual Service Logs (Existing) ✅

Your current setup already has dedicated terminals:

| Service | Task Name | Port | Panel |
|---------|-----------|------|-------|
| Chainlit UI | `🌿 Yonca AI: 🖥️ UI Start` | 8501 | Dedicated |
| FastAPI | `🌿 Yonca AI: ⚡ FastAPI Start` | 8000 | Dedicated |
| LangGraph | `🌿 Yonca AI: 🎨 LangGraph Start` | 2024 | Dedicated |
| Docker (all) | `🌿 Yonca AI: 🐳 Docker Logs` | Various | Dedicated |

### NEW: Master Logs Terminal ✅

**Task:** `🌿 Yonca AI: 📊 Master Logs`

Shows all Docker services in one terminal:
- Postgres logs
- Redis logs
- Ollama logs
- Langfuse logs

**How to use:**
1. Start services: Run `🌿 Yonca AI: 🚀 Start All`
2. View logs: Run `🌿 Yonca AI: 📊 Master Logs`
3. Individual terminals stay active for debugging

**Benefits:**
- Color-coded by service (automatic)
- Timestamps included (`--timestamps`)
- Tails last 50 lines per service
- Doesn't interfere with existing tasks

### What About Python Services?

**Current:** Each Python service (Chainlit, FastAPI, LangGraph) has its own terminal.

**Why not aggregated?**
- Windows doesn't have good tools for multi-process stdout aggregation
- Dedicated terminals are better for debugging (click links, scroll history)
- Docker logs task already covers infrastructure services

**For production:** Implement structured logging (see [LOG_AGGREGATION_GUIDE.md](LOG_AGGREGATION_GUIDE.md))

---

## 🗄️ Database Schema Rules

### ✅ You CAN Modify

| Table | Purpose | Safe to Change |
|-------|---------|----------------|
| `user_profiles` | Your business data | ✅ Yes |
| `farms` | Farm management | ✅ Yes |
| `parcels` | Land parcels | ✅ Yes |
| `alem_personas` | Synthetic farmers | ✅ Yes |
| Any other domain tables | Your logic | ✅ Yes |

### ❌ You CANNOT Modify

| Table | Purpose | Rule |
|-------|---------|------|
| `users` | Chainlit OAuth | ❌ **DO NOT TOUCH** |
| `threads` | Chainlit conversations | ❌ **DO NOT TOUCH** |
| `steps` | Chainlit messages | ❌ **DO NOT TOUCH** |
| `elements` | Chainlit attachments | ❌ **DO NOT TOUCH** |
| `feedbacks` | Chainlit reactions | ❌ **DO NOT TOUCH** |

**Why?**
- Chainlit enforces exact column names/types
- Breaking this causes silent failures
- Updates may conflict

**What if I need custom fields?**
- Use `metadata` JSON columns (e.g., `threads.metadata`)
- Create separate domain tables
- Link via foreign keys

### Example: Adding Farm Context to Threads

```python
# ❌ WRONG - Modifying Chainlit table
ALTER TABLE threads ADD COLUMN farm_id VARCHAR(20);

# ✅ CORRECT - Use metadata JSON
thread.metadata = {
    "farm_id": "F123",
    "expertise_areas": ["cotton"],
    "alem_persona_fin": "4F7U713"
}
```

---

## 📁 Where Are Things Stored?

### Database: PostgreSQL

```
Host: localhost:5433
Database: yonca
User: yonca
Password: yonca_dev_password

Tables:
├── Chainlit (UI persistence)
│   ├── users
│   ├── threads
│   ├── steps
│   ├── elements
│   └── feedbacks
│
└── Domain (Your business logic)
    ├── user_profiles
    ├── farms
    ├── parcels
    ├── alem_personas
    └── ... (add more as needed)
```

### Conversation Memory: Redis

```
Host: localhost:6379
Database: 0

Keys:
├── langgraph:checkpoint:* (LangGraph state)
├── session:* (App cache)
└── rate_limit:* (Rate limiting)
```

### Observability: Langfuse

```
Host: localhost:3001
Database: Separate Postgres (internal)

Data:
├── traces (LLM calls)
├── generations (Responses)
└── scores (Quality metrics)
```

---

## 🚨 Quick Rules

### Log Aggregation

| What | How | When |
|------|-----|------|
| View all Docker logs | Run `🌿 Yonca AI: 📊 Master Logs` | ✅ Available now |
| View Python service logs | Use dedicated terminals | ✅ Already working |
| Production log aggregation | Implement structured logging | 📅 Future |

### Database Modifications

| Action | Allowed? | Alternative |
|--------|----------|-------------|
| Add column to `users` | ❌ No | Use `metadata` JSON |
| Rename `threads.userId` | ❌ No | N/A — required by Chainlit |
| Add table `my_custom_table` | ✅ Yes | Create Alembic migration |
| Change `steps.createdAt` type | ❌ No | N/A — Chainlit expects VARCHAR |
| Index `user_profiles` | ✅ Yes | Add in migration |

---

## 📚 Full Documentation

- **Log Aggregation:** [LOG_AGGREGATION_GUIDE.md](LOG_AGGREGATION_GUIDE.md)
- **Schema Rules:** [CHAINLIT_SCHEMA_RULES.md](CHAINLIT_SCHEMA_RULES.md)
- **Chainlit Integration:** [demo-ui/docs/CHAINLIT-INTEGRATION-COMPLETE.md](demo-ui/docs/CHAINLIT-INTEGRATION-COMPLETE.md)

---

## 🎯 Common Tasks

### View Master Logs
```
1. Ctrl+Shift+P → Tasks: Run Task
2. Type "Master Logs"
3. Select "🌿 Yonca AI: 📊 Master Logs"
```

### Check Database Schema
```bash
# Connect to Postgres
psql -h localhost -p 5433 -U yonca -d yonca

# List tables
\dt

# Describe Chainlit tables
\d users
\d threads
\d steps
```

### Add Custom Table
```bash
# Generate migration
.\.venv\Scripts\alembic.exe revision -m "Add my_custom_table"

# Edit migration file
# Add op.create_table(...) in upgrade()

# Apply migration
.\.venv\Scripts\alembic.exe upgrade head
```

---

**Remember:**
- Master logs = Docker services only (good enough!)
- Chainlit tables = Read-only from your perspective
- Use `metadata` JSON for extensions
