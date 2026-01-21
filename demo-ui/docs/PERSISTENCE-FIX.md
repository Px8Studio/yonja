# Data Layer Persistence Fix

## Problem
```
2026-01-21 05:08:31 - WARNING - chainlit - SQLAlchemyDataLayer storage client is not initialized and elements will not be persisted!
```

**Root Cause**: Data layer was initialized but never registered with Chainlit due to redundant config flags.

## Solution Applied

### 1. Fixed Data Layer Registration Logic
**File**: [demo-ui/app.py](../app.py)

**Before**:
```python
# Required BOTH flags to be true
if demo_settings.enable_data_persistence and demo_settings.data_persistence_enabled:
    @cl.data_layer
    def _get_data_layer():
        return get_data_layer()
```

**After**:
```python
# Only checks if Postgres is configured
if demo_settings.data_persistence_enabled:
    @cl.data_layer
    def _get_data_layer():
        return get_data_layer()
```

**Why**: `data_persistence_enabled` already confirms Postgres availability. The extra `enable_data_persistence` check was redundant and caused the decorator to never register.

### 2. Conditional Initialization
**File**: [demo-ui/app.py](../app.py)

**Before**:
```python
# Always initialized, even for SQLite
try:
    asyncio.run(init_chainlit_data_layer())
except Exception as e:
    logger.error(f"Failed to initialize data layer: {e}")
```

**After**:
```python
# Only initializes when Postgres is configured
_data_layer_initialized = False
try:
    from config import settings as demo_settings_early
    if demo_settings_early.data_persistence_enabled:
        asyncio.run(init_chainlit_data_layer())
        _data_layer_initialized = True
        logger.info("✅ Data layer pre-initialized for Chainlit registration")
    else:
        logger.info("⏩ Skipping data layer init (SQLite/no Postgres configured)")
except Exception as e:
    logger.error(f"Failed to initialize data layer: {e}")
```

**Why**: Prevents unnecessary Postgres connection attempts when using SQLite (dev mode).

### 3. Enabled Postgres in Demo UI
**File**: [demo-ui/.env](../.env)

**Before**:
```dotenv
# DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca
# REDIS_URL=redis://localhost:6379/0
```

**After**:
```dotenv
DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca
REDIS_URL=redis://localhost:6379/0
ENABLE_DATA_PERSISTENCE=true
```

**Why**: Demo UI was falling back to SQLite. Now it uses the same Postgres DB as the main API.

### 4. Fixed Thread Resume Metadata Parsing
**File**: [demo-ui/app.py](../app.py) - `on_chat_resume()`

**Before**:
```python
metadata = thread.get("metadata", {})
cl.user_session.set("farm_id", metadata.get("farm_id", "demo_farm_001"))  # ❌ AttributeError if metadata is str
```

**After**:
```python
metadata = thread.get("metadata", {})
# Chainlit can store thread metadata as a JSON string in some setups
if isinstance(metadata, str):
    try:
        metadata = json.loads(metadata) if metadata.strip() else {}
    except Exception:
        metadata = {}
cl.user_session.set("farm_id", metadata.get("farm_id", "demo_farm_001"))  # ✅ Safe
```

**Why**: Chainlit sometimes serializes metadata as JSON string instead of dict. Now we handle both cases.

## Expected Behavior After Fix

### Startup Logs
```
2026-01-21 05:08:31 - INFO - app.py - Initializing Chainlit data layer with: localhost:5433/yonca
2026-01-21 05:08:31 - INFO - app.py - ✅ Chainlit data layer initialized successfully
2026-01-21 05:08:31 - INFO - app.py - ✅ Data layer pre-initialized for Chainlit registration
```

**No more warning**: `SQLAlchemyDataLayer storage client is not initialized`

### Thread Persistence
- ✅ Threads appear in sidebar after refresh
- ✅ Clicking "Resume" restores conversation
- ✅ Chat settings persist across sessions
- ✅ ALEM persona loads from database

### Database Tables Used
```
chainlit_users       → OAuth users (email, name, metadata)
chainlit_threads     → Conversation threads
chainlit_steps       → Individual messages
chainlit_elements    → Attachments, images, etc.
```

## Testing Steps

1. **Restart Demo UI**:
   ```powershell
   # Stop current UI (Ctrl+C)
   # Start fresh
   cd demo-ui
   chainlit run app.py -w --port 8501
   ```

2. **Verify Startup**:
   - Check logs for "✅ Data layer pre-initialized"
   - No "SQLAlchemyDataLayer storage client is not initialized" warning

3. **Test Thread Resume**:
   - Start a new conversation
   - Say something (e.g., "Salam")
   - Refresh browser (F5)
   - Click "Threads" in sidebar
   - Click your thread → Should resume without errors

4. **Test Settings Persistence**:
   - Open settings (⚙️ icon)
   - Change language to "English"
   - Refresh browser
   - Settings should be restored to English

## Config Reference

### When to Use Postgres vs SQLite

**Postgres (Recommended for Demo)**:
```dotenv
DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca
ENABLE_DATA_PERSISTENCE=true
```
- ✅ Threads persist across restarts
- ✅ User settings saved
- ✅ Multi-session support
- ✅ Production-ready

**SQLite (Dev Only)**:
```dotenv
DATABASE_URL=sqlite+aiosqlite:///./data/yonca.db
ENABLE_DATA_PERSISTENCE=false
```
- ⚠️  Session-only (threads lost on restart)
- ⚠️  No multi-user support
- ✅ Zero setup, good for quick tests

## Related Files
- [demo-ui/app.py](../app.py) - Main Chainlit app (data layer registration)
- [demo-ui/config.py](../config.py) - Config flags (`data_persistence_enabled`, `enable_data_persistence`)
- [demo-ui/data_layer.py](../data_layer.py) - YoncaDataLayer implementation
- [demo-ui/.env](../.env) - Environment variables (DATABASE_URL)
- [alembic/versions/add_chainlit_data_layer_tables.py](../../alembic/versions/add_chainlit_data_layer_tables.py) - Database schema

## Bonus Fix: Enhanced Logging

Added structured logging to track data layer initialization:
```python
logger.info("✅ Data layer pre-initialized for Chainlit registration")
logger.info("⏩ Skipping data layer init (SQLite/no Postgres configured)")
```

This makes it immediately clear whether persistence is active.
