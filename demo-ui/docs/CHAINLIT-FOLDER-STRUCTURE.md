# 📁 Chainlit Folder Structure — Yonca AI

## Overview

This document explains the proper Chainlit folder structure, why duplicate folders were created, and how we've cleaned them up.

---

## ✅ Correct Folder Structure

```
yonja/
├── demo-ui/                          # Chainlit app root (working directory)
│   ├── .chainlit/                    # ✅ CORRECT: App config folder
│   │   ├── config.toml              # ✅ Track in git
│   │   ├── oauth.json               # ✅ Track in git
│   │   └── translations/
│   │       ├── az-AZ.json           # ✅ Track (custom Azerbaijani)
│   │       ├── en-US.json           # ✅ Track (English, built-in)
│   │       ├── ru-RU.json           # ✅ Track (custom Russian)
│   │       └── *.json               # ❌ Ignore (auto-generated, 19+ files)
│   │
│   ├── .chainlitignore              # ✅ Prevent .files/ folder creation
│   ├── app.py                       # Main Chainlit application
│   ├── data_layer.py                # PostgreSQL persistence
│   ├── storage_postgres.py          # PostgreSQL file storage (replaces .files/)
│   └── public/                      # Static assets (CSS, JS, avatars)
│
├── .chainlit/                       # ❌ DELETED: Was created accidentally
├── .files/                          # ❌ DELETED: Unused local file cache
└── .gitignore                       # ✅ Updated to ignore unnecessary files
```

---

## 🔍 Why Were There Two `.chainlit` Folders?

### Root Cause
Chainlit creates its `.chainlit` configuration folder in the **current working directory** where `chainlit run` is executed.

### What Happened
1. **Root `.chainlit/`** was created when someone ran `chainlit run demo-ui/app.py` from the **project root**
2. **demo-ui/.chainlit/** was created when running from **inside demo-ui/** (correct)

### Why This is Confusing
- Both folders can coexist, but only one is actually used
- The active config depends on where you run the command
- Our VS Code task runs from `demo-ui/` (correct), so only `demo-ui/.chainlit/` is used

---

## 📦 What is the `.files/` Folder?

### Purpose
Chainlit's default **local file storage** for spontaneous uploads (images, audio, PDFs).

### Why We Don't Use It
We implemented **PostgreSQL-based file storage** ([storage_postgres.py](storage_postgres.py)) instead:
- ✅ **Data sovereignty** — All data in one database
- ✅ **Single backup** — Files included in DB backups
- ✅ **ACID compliance** — Transactional file operations
- ❌ `.files/` would be redundant and create clutter

### Solution
- Created [.chainlitignore](.chainlitignore) to prevent `.files/` creation
- Deleted empty `.files/` folders from both locations

---

## 🗂️ Translation Files

### The Problem
Chainlit auto-generates **22 translation files** on first run (en-US, fr-FR, de-DE, zh-CN, etc.).

### What We Need
- `az-AZ.json` — Azerbaijani (primary user language)
- `en-US.json` — English (fallback)
- `ru-RU.json` — Russian (optional support)

### Solution
Updated [.gitignore](../.gitignore) to:
```gitignore
# Ignore all auto-generated translations
demo-ui/.chainlit/translations/*.json

# Track only required languages
!demo-ui/.chainlit/translations/az-AZ.json
!demo-ui/.chainlit/translations/en-US.json
!demo-ui/.chainlit/translations/ru-RU.json
```

---

## ⚙️ Disabled Chainlit Features

To reduce UI noise for farmers, we disabled features in [.chainlit/config.toml](config.toml):

| Feature | Status | Reason |
|---------|--------|--------|
| `allow_thread_sharing` | ❌ Disabled | Requires `on_shared_thread_view` callback (not implemented) |
| `favorites` | ❌ Disabled | Adds ⭐ button clutter — farmers can scroll to find messages |
| `features.mcp.*` | ❌ Disabled | Model Context Protocol not implemented — removes 🔌 plug icon |
| `prompt_playground` | ❌ Disabled | For developers, not end users |
| `latex` | ❌ Disabled | No mathematical notation needed |

### What Stays Enabled
- ✅ `unsafe_allow_html` — For dashboard cards (AI-generated only)
- ✅ `features.audio` — Voice input for farmers
- ✅ `features.spontaneous_file_upload` — Image/PDF uploads (images/*, application/pdf)
- ✅ `edit_message` — Users can fix typos
- ✅ `auto_tag_thread` — Threads tagged with chat profile

---

## 🔒 Security Notes

### OAuth Configuration
[oauth.json](oauth.json) contains **only scopes**, not secrets:
```json
{
  "google": {
    "scopes": ["openid", "email", "profile"]
  }
}
```

Actual credentials are in `.env`:
```bash
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-secret
```

### File Upload Security
[config.toml](config.toml) restricts uploads to:
```toml
accept = ["image/*", "application/pdf"]  # No executables
max_files = 10
max_size_mb = 100
```

---

## 🚀 Running the App

### From VS Code (Recommended)
Run task: **🌿 Yonca AI: 🚀 Start All**

This executes:
```bash
chainlit run app.py -w --port 8501 --headless
```

With working directory: `${workspaceFolder}/demo-ui` ✅

### From Terminal
```bash
cd demo-ui
chainlit run app.py -w --port 8501
```

**DO NOT** run from project root:
```bash
# ❌ WRONG: Creates root .chainlit/ folder
chainlit run demo-ui/app.py
```

---

## 📋 Verification Checklist

After cleanup, verify:
- [ ] Only `demo-ui/.chainlit/` exists (not root `.chainlit/`)
- [ ] No `.files/` folders anywhere
- [ ] Only 3 translation files tracked in git (az-AZ, en-US, ru-RU)
- [ ] `.chainlitignore` exists in demo-ui/
- [ ] Task runs from `demo-ui/` working directory
- [ ] App starts without creating unwanted folders

---

## 🔗 Related Documentation

- [Chainlit Data Persistence](https://docs.chainlit.io/data-persistence/overview)
- [PostgreSQL File Storage](storage_postgres.py)
- [Chainlit Configuration Reference](https://docs.chainlit.io/configuration)
- [OAuth Setup Guide](../docs/zekalab/11-CHAINLIT-UI.md)

---

**Last Updated:** January 23, 2026
**Maintained By:** ZekaLab Team
