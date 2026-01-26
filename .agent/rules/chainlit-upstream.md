# Chainlit Upstream Parity — Agent Instructions

> **Scope:** Rules for maintaining parity with Chainlit upstream releases.
> **Canonical Source:** https://github.com/Chainlit/chainlit
> **Current Version:** 2.9.6 (as of 2026-01-24)

---

## 📋 Before Modifying Chainlit UI Code

### Always Check

1. **CHANGELOG First**
   ```
   https://github.com/Chainlit/chainlit/blob/main/CHANGELOG.md
   ```
   Review recent releases for new features, breaking changes, or deprecations.

2. **Current Version**
   ```bash
   grep chainlit pyproject.toml  # Should match ^2.9.6 or later
   ```

3. **Docs for New Features**
   ```
   https://docs.chainlit.io/
   ```

---

## 🔄 Version Tracking

| Date | Version | Key Changes | Applied? |
|------|---------|-------------|----------|
| 2026-01-20 | 2.9.6 | Date picker widget, toggle_chat_settings, skip new chat confirmation | ⏳ |
| 2026-01-08 | 2.9.5 | Favorite messages (prompt templates) | ✅ (favorites=true) |
| 2025-12-24 | 2.9.4 | Modes (model/planning/reasoning), shared thread icon | ⏳ |
| 2025-12-04 | 2.9.3 | Native video in markdown, OAuth tests | N/A |
| 2025-11-22 | 2.9.2 | PostgreSQL data layer (official) | ✅ |

---

## ✅ Currently Used Features

These are enabled in `.chainlit/config.toml`:

| Feature | Config Key | Status |
|---------|------------|--------|
| Data persistence | `@cl.data_layer` | ✅ PostgreSQL |
| OAuth | `[providers.google]` | ✅ Google |
| Audio input | `[features.audio]` | ✅ 16kHz |
| MCP integration | `[features.mcp]` | ✅ SSE/HTTP/stdio |
| File uploads | `[features.spontaneous_file_upload]` | ✅ images, PDF |
| Chat profiles | `@cl.set_chat_profiles` | ✅ LLM models |
| Thread sharing | `allow_thread_sharing` | ✅ |
| Prompt playground | `prompt_playground` | ✅ |
| LLM playground | `[features.llm_playground]` | ✅ |
| Custom CSS/JS | `custom_css`, `custom_js` | ✅ |
| Favorites | `favorites` | ✅ |
| Chat settings | `chat_settings_location = "sidebar"` | ✅ |

---

## ⚠️ Not Yet Used (Consider Implementing)

| Feature | Version Added | Priority | Notes |
|---------|---------------|----------|-------|
| **Date Picker Widget** | 2.9.6 | HIGH | Use for `planning_month` setting |
| **toggle_chat_settings()** | 2.9.6 | MEDIUM | Programmatic settings panel control |
| **Modes** | 2.9.4 | HIGH | Native model/planning selector |
| **@cl.set_starters** | 2.0+ | HIGH | Profile-aware starters (replace manual buttons) |
| **Native Feedback** | 2.0+ | MEDIUM | Use instead of custom feedback buttons |
| **Custom Elements** | 2.8+ | LOW | React components (advanced) |

---

## 🚫 Deprecated / Avoid

| Pattern | Reason | Use Instead |
|---------|--------|-------------|
| `chat_starters` list | Deprecated | `@cl.set_starters` decorator |
| Inline HTML in Python | Security risk | CSS classes in custom.css |
| `print()` for logging | Not structured | `structlog` via `get_logger()` |

---

## 🔧 Upgrade Procedure

When upgrading Chainlit version:

1. **Review CHANGELOG** from current → target version
2. **Run database migrations** if any:
   ```sql
   -- Example from 2.9.4:
   ALTER TABLE steps ADD COLUMN IF NOT EXISTS modes JSONB;
   ```
3. **Update `pyproject.toml`**:
   ```toml
   chainlit = "^2.9.x"
   ```
4. **Sync `demo-ui/requirements.txt`** with pyproject.toml
5. **Test OAuth flow** — authentication changes often
6. **Test data persistence** — schema may change

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `.chainlit/config.toml` | Feature flags, OAuth, UI settings |
| `.chainlit/translations/` | i18n files (az-AZ.json) |
| `public/custom.css` | UI styling |
| `public/custom.js` | PWA, MCP badge |
| `data_layer.py` | PostgreSQL persistence |
| `app.py` | Lifecycle handlers |

---

## 🔗 References

- [Chainlit CHANGELOG](https://github.com/Chainlit/chainlit/blob/main/CHANGELOG.md)
- [Chainlit Docs](https://docs.chainlit.io/)
- [Chainlit GitHub Releases](https://github.com/Chainlit/chainlit/releases)
- [Community Discussions](https://github.com/Chainlit/chainlit/discussions)
