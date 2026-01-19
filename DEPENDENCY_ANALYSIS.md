# Dependency & Environment Issues Analysis

**Date:** January 19, 2026  
**Status:** 🚨 Critical Issues Found

---

## 🔴 Issue #1: Missing LangGraph Checkpoint Packages (Recurring)

### What's Happening
```
[debug    ] 🌾 🔴 langgraph-checkpoint-redis not installed
[debug    ] 🌾 🐘 langgraph-checkpoint-postgres not installed
```

### Why This Happens

**Root Cause:** Two separate Python environments with different dependency management:

1. **Backend (`pyproject.toml`)** - Poetry-managed
   - Has `langgraph-checkpoint-redis = "^0.3.2"` ✅
   - Has `langgraph-checkpoint-postgres = "^3.0.0"` ✅
   - Located: `C:\Users\rjjaf\_Projects\yonja\.venv\`

2. **Demo UI (`demo-ui/requirements.txt`)** - pip-managed  
   - ❌ **MISSING** both checkpoint packages!
   - Located: `C:\Users\rjjaf\_Projects\yonja\demo-ui\.venv\`
   - Dependencies install fresh each time → missing packages disappear

### Current Flow
```
Root .venv (Poetry)             Demo UI .venv (pip)
├── langgraph ✅               ├── langgraph ✅
├── checkpoint-redis ✅        ├── checkpoint-redis ❌
├── checkpoint-postgres ✅     ├── checkpoint-postgres ❌
└── ...                        └── ...
```

### Why They Keep Disappearing
- Chainlit runs in isolated `demo-ui/.venv`
- When you run `pip install -r requirements.txt`, checkpoint packages aren't there
- Next environment refresh → reinstall → packages gone again
- This is a **per-environment isolation problem**

---

## 🔴 Issue #2: PostgreSQL Checkpointer Not Used (Fallback to In-Memory)

### What's Happening
```
[info     ] 🌾 💾 Using in-memory checkpointer (no persistence)
Skipping PostgreSQL checkpointer: langgraph-checkpoint-postgres not installed
```

### Root Cause
The Chainlit environment doesn't have `langgraph-checkpoint-postgres` installed, so:

```python
# demo-ui/app.py (hypothetical, from logs)
try:
    from langgraph.checkpoint.postgres import PostgresCheckpointer
except ImportError:
    # Falls back to in-memory (no persistence!)
    logger.debug("Skipping PostgreSQL checkpointer: langgraph-checkpoint-postgres not installed")
```

**Impact:**
- ⚠️ LangGraph state NOT persisted to database
- Session state lost on server restart
- Can't resume conversations across deployments
- Fine for development, **CRITICAL for production**

---

## 🔴 Issue #3: Missing "Weather" Action Callback

### What's Happening
```
Not Found: No callback found for action weather!
```

### Root Cause
In [demo-ui/app.py](demo-ui/app.py):
- **Line 431:** Defines weather starter button
- **Line 1146-1148:** Defines weather action UI element
- **BUT:** No `@cl.on_action` handler for "weather" action

```python
# Action is TRIGGERED (line 1146-1148):
cl.Action(
    name="weather",
    payload={"action": "weather"},
    label=AZ_STRINGS["weather"],
)

# But NO HANDLER like:
# @cl.on_action("weather")
# async def handle_weather_action(action: cl.Action):
#     ...
```

### Why This Is Different from `@on_message`

The comment in app.py (line 1181) says:
```python
# "When user clicks starter → Message sent → @on_message handles it"
# "No separate action callbacks needed!"
```

**But this is WRONG** - Actions don't auto-convert to messages. They need explicit handlers.

---

## 📊 Environment Architecture Comparison

### Current Setup (Two Separate venvs)
```
Project Root
│
├── pyproject.toml (Poetry)
│   └── .venv/ (Backend)
│       ├── fastapi
│       ├── langgraph ✅
│       ├── checkpoint-redis ✅  
│       ├── checkpoint-postgres ✅
│       └── ...
│
└── demo-ui/
    ├── requirements.txt (pip)
    │   └── .venv/ (Chainlit UI)
    │       ├── chainlit
    │       ├── langgraph ✅
    │       ├── checkpoint-redis ❌  ← MISSING
    │       ├── checkpoint-postgres ❌  ← MISSING
    │       └── ...
    └── app.py
```

### Issues with Current Approach
1. **Dependency Duplication** - langgraph installed in both venvs
2. **Missing in UI** - checkpoint packages not in requirements.txt
3. **Harder to Debug** - Which venv is running? Which has the right packages?
4. **Harder to Sync** - Update one, forget the other
5. **CI/CD Risk** - Different installs in dev vs. production

---

## ✅ Recommended Fixes (Priority Order)

### Fix #1: Add Missing Packages to demo-ui/requirements.txt (IMMEDIATE)
```diff
+ langgraph-checkpoint-redis>=0.3.0
+ langgraph-checkpoint-postgres>=3.0.0
```

**Impact:** Fixes both the "missing packages" warning AND enables PostgreSQL persistence  
**Effort:** 2 minutes  
**Risk:** None (additive only)

### Fix #2: Implement Weather Action Callback (IMMEDIATE)
Add `@cl.on_action` handler in [demo-ui/app.py](demo-ui/app.py):
```python
@cl.on_action
async def handle_action(action: cl.Action):
    """Handle quick-action buttons: weather, subsidy, irrigation."""
    action_type = action.payload.get("action")
    
    if action_type == "weather":
        # Generate weather forecast for user's farm
        ...
    elif action_type == "subsidy":
        # Show subsidy information
        ...
    elif action_type == "irrigation":
        # Irrigation recommendations
        ...
    else:
        logger.warning(f"unknown_action", action=action_type)
```

**Impact:** Fixes "No callback found" error  
**Effort:** 30 minutes (need to implement weather/subsidy/irrigation logic)  
**Risk:** Low (handlers are optional until clicked)

### Fix #3: Consolidate to Single pyproject.toml (OPTIONAL - FUTURE)
**Approach:** One Poetry project, multiple entry points:

```
yonja/
├── pyproject.toml (manages all dependencies)
├── src/yonca/ (backend code)
├── demo-ui/ (Chainlit UI)
├── tests/
└── .venv/ (single shared environment)
```

**Benefits:**
- One source of truth for dependencies
- Easier to keep in sync
- Simpler CI/CD
- Better for team development

**Trade-off:** Requires restructuring, but more maintainable long-term

---

## 🔧 Implementation Plan

### Immediate (Today)
- [ ] Add checkpoint packages to `demo-ui/requirements.txt`
- [ ] Reinstall demo-ui venv: `pip install -r demo-ui/requirements.txt`
- [ ] Verify packages present: `pip list | grep langgraph-checkpoint`
- [ ] Implement weather action callback

### Short-term (This Week)
- [ ] Test persistence: Restart LangGraph, verify session state persists
- [ ] Implement subsidy & irrigation action callbacks
- [ ] Document all quick-action flows

### Medium-term (This Sprint)
- [ ] Evaluate single-pyproject consolidation
- [ ] Create migration plan if consolidation approved
- [ ] Update CI/CD to match chosen approach

---

## 🚨 Foreign Key Constraint Error (Secondary Issue)

### What's Happening
```
[error    ] save_persona_failed
            error='(sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) ... 
            violates foreign key constraint "alem_personas_chainlit_user_id_fkey"
            Key (chainlit_user_id)=(info@px8.studio) is not present in table "users".'
```

### Root Cause
User being created in `alem_personas` table, but not first in `users` table.

**Fix Already In Place:**
[Line 1367](demo-ui/app.py#L1367) has:
```python
if user:
    from data_layer import ensure_user_persisted
    user_persisted = await ensure_user_persisted(user)
```

But apparently this isn't working. May need debugging, but secondary to checkpoint issue.

---

## Summary

| Issue | Severity | Root Cause | Fix Effort |
|-------|----------|-----------|-----------|
| Missing checkpoint packages | 🔴 High | Not in requirements.txt | 2 min |
| No PostgreSQL persistence | 🔴 High | Packages not installed | Auto-fixed by #1 |
| Missing weather callbacks | 🟡 Medium | Handler not implemented | 30 min |
| Environment duplication | 🟡 Medium | Two separate pyproject/requirements | 1-2 days |
| Foreign key error | 🟡 Medium | User not persisted first | TBD |

