# Chainlit UI/UX — Agent Guidelines

> **Scope:** This file contains rules for the AI coding assistant when working on Chainlit frontend code in `demo-ui/`.
> **Last Updated:** 2026-01-24

---

## 🎯 Design Philosophy

### Core Principles

1. **Mobile-First, Farmer-First**
   - Target users are farmers in the field, often on phones
   - Touch targets must be ≥44px
   - Text must be readable in sunlight (high contrast)
   - Prefer simple actions over complex menus

2. **Natural Tech Aesthetic**
   - Use 🌿 clover emoji as brand element (ALEM = Ağıllı Lem = Smart Clover)
   - Glassmorphism for modern feel (`backdrop-filter: blur()`)
   - Forest green palette: `#2D5A27` (primary), `#A8E6CF` (light)
   - Avoid harsh reds/oranges except for errors

3. **Azerbaijani-First UX**
   - All user-facing text in Azerbaijani (AZ)
   - Use formal "siz" (you-formal), not "sən" (you-informal)
   - Numbers: use space separator (1 000 ha, not 1,000 ha)

---

## 🏗️ Architecture Rules

### File Locations

| What | Where | Rule |
|------|-------|------|
| Lifecycle handlers | `app.py` | `@cl.on_chat_start`, `@cl.on_message`, etc. |
| Loading states | `components/spinners.py` | All spinner text/styles |
| Custom components | `components/` | Farm selector, status badges |
| Styling | `public/custom.css` | NO inline styles in Python |
| Configuration | `.chainlit/config.toml` | Feature flags, OAuth |
| Static assets | `public/` | CSS, JS, images, avatars |

### Handler Patterns

```python
# ✅ CORRECT: Use LoadingStates for all spinners
from components.spinners import LoadingStates
thinking_msg = cl.Message(content=LoadingStates.thinking())

# ❌ WRONG: Hardcoded spinner text
thinking_msg = cl.Message(content="Düşünürəm...")

# ✅ CORRECT: Store session state in cl.user_session
cl.user_session.set("farm_id", "F123")

# ❌ WRONG: Global variables for session state
_current_farm_id = "F123"  # Don't do this!
```

---

## 🔄 UI States — Must Understand

### The 5 Lifecycle States

1. **Initial Load** — Chainlit's built-in React spinner (NOT controllable via Python)
2. **`on_chat_start`** — Session initialization, welcome dashboard
3. **`on_chat_resume`** — Thread restoration after refresh
4. **`on_message`** — Main conversation handling
5. **`on_settings_update`** — User preference changes

### Loading Spinner States

Always use `LoadingStates` class from `components/spinners.py`:

| State | Use When |
|-------|----------|
| `LoadingStates.thinking()` | Agent reasoning |
| `LoadingStates.loading_data()` | Fetching from DB |
| `LoadingStates.searching_knowledge()` | RAG/vector search |
| `LoadingStates.transcribing_audio()` | Whisper STT |
| `LoadingStates.analyzing_farm()` | Farm data analysis |
| `LoadingStates.generating_advice()` | Creating recommendations |

---

## ❌ Forbidden Patterns

### Never Do

1. **Modify Chainlit table schemas** — See `docs/CHAINLIT_SCHEMA_RULES.md`
2. **Use inline HTML in Python** — Use CSS classes in `custom.css`
3. **Skip `await` on cl.Message** — Always `await msg.send()`
4. **Store secrets in session** — `cl.user_session` is client-visible
5. **Use `print()` for logging** — Use `structlog` logger

### Avoid

1. **Multiple sequential messages** — Consolidate into single welcome
2. **Blocking MCP calls in `on_chat_start`** — Consider background init
3. **Raw exception messages to users** — Wrap in friendly Azerbaijani

---

## ✅ Required Patterns

### When Adding New UI Elements

1. **Add spinner state** → Update `components/spinners.py`
2. **Add action button** → Create `@cl.action_callback` handler
3. **Add settings widget** → Update `setup_chat_settings()` in `app.py`
4. **Add visual styling** → Edit `public/custom.css`, not inline

### When Modifying Welcome Flow

1. Check `send_dashboard_welcome()` function
2. Update quick action buttons if needed
3. Test with OAuth enabled AND disabled
4. Verify MCP status display

### When Adding Audio Features

1. Handle all 3 audio lifecycle events:
   - `@cl.on_audio_start` — Return True to allow
   - `@cl.on_audio_chunk` — Buffer if streaming
   - `@cl.on_audio_end` — Process and respond

---

## 📁 Key Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~2800 | Main application, all handlers |
| `components/spinners.py` | 248 | Loading states |
| `public/custom.css` | ~1000 | All visual styling |
| `.chainlit/config.toml` | 269 | Features, OAuth, UI settings |
| `data_layer.py` | ~600 | PostgreSQL persistence |
| `chainlit.md` | 15 | Welcome screen markdown |

---

## 🌐 Internationalization

### Current Languages

- **az-AZ** — Azerbaijani (primary)
- **en-US** — English (fallback)
- **ru-RU** — Russian (optional)

### Adding User-Facing Text

1. Add to `SPINNER_MESSAGES` in `spinners.py` (Azerbaijani)
2. Consider adding English fallback
3. Use formal tone ("Sizin" not "Sənin")

---

## 🧪 Testing Chainlit Changes

```powershell
# Start services
cd demo-ui
chainlit run app.py -w --port 8501

# Test scenarios:
# 1. Fresh browser (incognito) — on_chat_start
# 2. Refresh existing session — on_chat_resume
# 3. Audio input — on_audio_* handlers
# 4. Settings change — on_settings_update
```

---

## 🔗 Related Documentation

- [11-CHAINLIT-UI.md](../../docs/zekalab/11-CHAINLIT-UI.md) — Full UI guide
- [11-CHAINLIT-STRUCTURE.md](../../docs/zekalab/11-CHAINLIT-STRUCTURE.md) — Folder structure
- [CHAINLIT_SCHEMA_RULES.md](../../docs/CHAINLIT_SCHEMA_RULES.md) — Database rules
- [Chainlit Official Docs](https://docs.chainlit.io) — Upstream reference
