# Quick-Start: Chat Issues & UI Refresh - FIXES APPLIED

## ✅ What Was Fixed

### 1. **Session State Lost on Refresh**
- **Problem**: User preferences, farm selection, expertise areas disappeared when page was refreshed
- **Root Cause**: Session data only in-memory; lost when Chainlit recreates session
- **Solution**: `SessionManager` class persists all preferences to PostgreSQL
- **Files Added**:
  - `demo-ui/services/session_manager.py` - Unified session state management

### 2. **MCP Server Initialization Race Condition**
- **Problem**: MCP tools failed to load if server wasn't ready on startup
- **Root Cause**: Initial MCP health check failed, then succeeded later
- **Solution**: `MCPResilienceManager` implements exponential backoff retry
- **Files Added**:
  - `demo-ui/services/mcp_resilience.py` - Retry logic with graceful degradation
- **Behavior**:
  - Retries MCP initialization up to 3 times
  - Delays: 1s → 2s → 4s (exponential backoff)
  - If all retries fail, continues without tools (graceful degradation)

### 3. **Updated @cl.on_chat_start**
- Now calls `initialize_session_with_persistence()` to restore user preferences from DB
- Now uses `initialize_mcp()` with resilience layer instead of direct MCP calls
- File Updated: `demo-ui/app.py` (lines 2315-2670)

---

## 🧪 How to Test

### Test 1: Session Persistence After Refresh
1. Open chat UI: http://localhost:8501
2. Select a farm from the dropdown (if available)
3. Change chat profile (Ask → Plan → Agent)
4. **Refresh the page** (F5 or Cmd+R)
5. ✅ **Expected**: Farm selection and chat profile should be restored

### Test 2: MCP Graceful Degradation
1. Make sure MCP server is running: http://localhost:7777/health
2. Open chat UI
3. ✅ **Expected**: "MCP tools available" message in welcome
4. Now kill the MCP server: `docker stop yonca-mcp` (or equivalent)
5. Refresh the chat UI
6. ✅ **Expected**:
   - Retry attempts logged in terminal
   - After 3 retries (~7 seconds), shows "MCP tools unavailable"
   - Chat still works (no tools, but continues)

### Test 3: MCP Auto-Recovery
1. With MCP down and retry exhausted
2. Restart MCP: `docker start yonca-mcp`
3. Send a message to the chat
4. ✅ **Expected**: Chat should still work; next @cl.on_chat_start retry will find MCP

---

## 📋 Architecture Changes

### Before
```
Chainlit UI
    ↓ (Direct)
LangGraph Server
    ↓
MCP Server
[Session lost on refresh]
[MCP failures crash entire session]
```

### After
```
Chainlit UI
    ↓ (HTTP)
SessionManager (persists to DB)
LangGraphClient
    ↓
MCPResilienceManager (retry + degradation)
    ↓
LangGraph Server
    ↓
MCP Server (optional)

[Session restored on refresh]
[MCP failures gracefully handled]
```

---

## 🔧 Configuration

### SessionManager (Default: Enabled if PostgreSQL is configured)
Session data is persisted to Chainlit's data layer (PostgreSQL).

**Environment Variables:**
```bash
DATABASE_URL=postgresql+asyncpg://yonca:password@localhost:5433/yonca
```

**What's Persisted:**
- Chat profile (Ask/Plan/Agent mode)
- Farm selection
- Expertise areas
- Language preference
- Detail level (Qısa/Orta/Ətraflı)

### MCPResilienceManager Configuration
```python
# In demo-ui/app.py on_chat_start
mcp_url = os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777")
mcp_initialized = await initialize_mcp(mcp_url=mcp_url)
```

**Environment Variables:**
```bash
ZEKALAB_MCP_URL=http://localhost:7777
```

**Retry Configuration (in mcp_resilience.py):**
```python
max_retries=3                    # 3 retry attempts
initial_delay=1.0              # Start with 1 second
backoff_factor=2.0             # Double each retry
max_delay=10.0                 # Never exceed 10 seconds
```

---

## 🐛 Debugging

### Check Session Persistence
```python
# In a terminal, with chat UI running:
from services.session_manager import SessionManager
import asyncio

async def test():
    prefs = await SessionManager.load_user_preferences("contact@zekalab.info")
    print(prefs)

asyncio.run(test())
```

### Check MCP Status
```python
from services.mcp_resilience import get_mcp_status

status = get_mcp_status()
print(status)
# Output:
# {
#   'available': True,
#   'url': 'http://localhost:7777',
#   'last_check': '2026-01-24T00:15:30.123456',
#   'last_error': None,
#   'retry_attempts': 2
# }
```

### Enable Debug Logging
```bash
# In terminal
ZEKALAB_LOG_LEVEL=DEBUG chainlit run demo-ui/app.py
```

**Look for these log lines:**
```
session_preferences_loaded       # Session restored
session_preferences_saved        # Session updated
mcp_resilience_initialized       # MCP ready
mcp_initialization_retry         # MCP retry attempt
```

---

## 📊 What's NOT Fixed Yet

These were identified but require more work:

### 1. **Three UIs Confusion** (Architecture Issue)
- **Problem**: You have Chainlit UI, FastAPI REST, and MCP Server
- **Solution**: Requires refactoring to separate frontend/backend
- **Timeline**: Phase 2+ (2-3 weeks)

### 2. **UI State Loss on Error** (Edge Case)
- **Problem**: If LangGraph server crashes mid-chat, state lost
- **Solution**: Implement checkpoint/recovery system
- **Timeline**: Phase 2

### 3. **MCP Tool Loading** (Startup Performance)
- **Problem**: MCP tool loading is slow (~3-5 seconds)
- **Solution**: Lazy load tools on demand, not on startup
- **Timeline**: Phase 3

---

## ✨ Quick Wins for Next Steps

### 1. **Monitor MCP Health in Real-Time** (15 min)
Add background task to check MCP every 60 seconds:
```python
@cl.on_chat_start
async def check_mcp_periodic():
    while True:
        await asyncio.sleep(60)
        manager = get_mcp_manager()
        await manager.health_check()
        if manager.is_available:
            logger.info("mcp_still_online")
```

### 2. **Save Chat Profile on Selection** (20 min)
Hook into chat profile dropdown change:
```python
@cl.on_chat_profile_change
async def on_profile_change(profile: str):
    user_id = cl.user_session.get("user_email")
    await SessionManager.save_interaction_mode(user_id, profile)
    logger.info("chat_profile_changed_and_persisted", profile=profile)
```

### 3. **Add "Save Preferences" Button** (30 min)
Explicit save so users know state is persisted:
```python
async def save_all_preferences():
    user_id = cl.user_session.get("user_email")
    prefs = cl.user_session.get("user_preferences", {})
    await SessionManager.save_custom_preferences(user_id, **prefs)
    await cl.Message(content="✅ Preferences saved", author="System").send()
```

---

## 🎯 Expected Behavior After Fixes

### Scenario 1: Normal Refresh
1. User selects farm, changes mode to "Agent", adjusts language
2. User presses F5 (refresh)
3. **Before**: Everything lost, default state
4. **After**: Farm + mode + language restored

### Scenario 2: MCP Offline at Startup
1. MCP server is down
2. User opens chat (Chainlit starts)
3. **Before**: Chat fails, user sees error
4. **After**: "⚠️ MCP tools unavailable - chat continues without tools"
5. **Later**: MCP comes back online, tools available in next session

### Scenario 3: MCP Comes Online During Session
1. MCP is down, user already chatting without tools
2. MCP server starts
3. **Before**: Still no tools (would need to refresh)
4. **After**: Next chat message will have tools (auto-recovery)

---

## 📝 Files Changed/Created

### Created
- `demo-ui/services/session_manager.py` (180 lines)
- `demo-ui/services/mcp_resilience.py` (250 lines)
- `ARCHITECTURE_ANALYSIS.md` (comprehensive architecture doc)

### Modified
- `demo-ui/app.py`
  - Added imports for SessionManager + MCPResilienceManager (4 lines)
  - Updated @cl.on_chat_start to use persistence + resilience (30 lines modified)

### Total Code Added: ~450 lines
### Breaking Changes: None (backward compatible)
### Migration Required: No (no database schema changes)

---

## 🚀 Next Steps

1. **Test the fixes** using scenarios above
2. **Monitor logs** for session persistence and MCP resilience
3. **Optional**: Implement quick wins (background health check, save button)
4. **Phase 2**: Refactor UI/API separation (planned for later)

---

## ❓ FAQ

**Q: Will this work with SQLite (no Postgres)?**
A: Yes! If PostgreSQL not configured, falls back gracefully to in-memory session.

**Q: What if user closes browser completely?**
A: On next login, if OAuth is enabled, SessionManager loads persisted data from DB.

**Q: Does this affect chat history?**
A: No, chat history is separate. This only persists user preferences.

**Q: Can I customize retry delays?**
A: Yes, edit `MCPResilienceManager` init in `mcp_resilience.py` or set in config.

**Q: What happens if both retries and MCP fail?**
A: Chat continues without MCP tools. System message shows "⚠️ MCP tools unavailable".

---

## 📞 Support

If issues occur:
1. Check logs: `grep -i "session\|mcp\|resilience" logs/`
2. Debug with: `ZEKALAB_LOG_LEVEL=DEBUG`
3. Test manually with provided scenarios
4. Open issue with logs attached
