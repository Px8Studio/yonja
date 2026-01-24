# 📁 Chainlit Folder Structure — ALİM

## Overview

This document explains the standard Chainlit folder structure used in the **ALİM** project. It adheres to Chainlit best practices while integrating with our custom architecture (PostgreSQL persistence).

## ✅ Project Structure

```
yonja/
├── demo-ui/                          # Chainlit app root (working directory)
│   ├── .chainlit/                    # ✅ ESSENTIAL: App config folder
│   │   ├── config.toml              # Main configuration (Tracked)
│   │   ├── oauth.json               # OAuth scopes (Tracked)
│   │   └── translations/            # UI Translations
│   │       ├── az-AZ.json           # Azerbaijani (Custom)
│   │       ├── en-US.json           # English (Built-in)
│   │       └── ru-RU.json           # Russian (Custom)
│   │
│   ├── .chainlitignore              # ✅ ESSENTIAL: Prevents creating local cache
│   ├── app.py                       # Main Chainlit application (Entry point)
│   ├── constants.py                 # UI Constants & Configuration
│   ├── services/                    # Modular business logic
│   │   ├── expertise.py             #     - Persona & expertise logic
│   │   ├── mode_resolver.py         #     - LLM mode selection
│   │   └── thread_utils.py          #     - Thread management
│   ├── data_layer.py                # PostgreSQL persistence
│   ├── storage_postgres.py          # PostgreSQL file storage
│   └── public/                      # Static assets (CSS, JS, avatars)
```

### Key Folders Explained

#### 1. `.chainlit/` (Configuration)
This folder **must** exist in the directory where you run `chainlit run`. It controls the UI appearance, features, and authentication.
*   **config.toml**: Disables unnecessary features (like prompt playground) to keep the UI clean for farmers.
*   **translations/**: Contains localization files. We track only the ones we support (`az-AZ`, `en-US`, `ru-RU`) and ignore auto-generated ones via `.gitignore`.

#### 2. `.files/` (File Storage) — **DISABLED**

> [!IMPORTANT]
> **ALİM does NOT use local `.files/` storage.**
> We use **PostgreSQL** for file storage. This is a **production best practice**.

---

## 🏭 Production Storage Architecture

### The Problem with `.files/` (Local Storage)

In modern cloud engineering (Docker, Kubernetes, Render), applications must be **stateless**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  THE PROBLEM: Local File Storage in Cloud Deployments                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Scenario 1: Container Restart                                         │
│  ┌─────────────────┐         ┌─────────────────┐                       │
│  │   Container     │  crash  │   New Container │                       │
│  │   .files/       │ ──────► │   .files/ = ∅   │  ← Files LOST!       │
│  │   └── image.png │         └─────────────────┘                       │
│  └─────────────────┘                                                   │
│                                                                         │
│  Scenario 2: Load Balancer                                             │
│  ┌─────────────────┐                                                   │
│  │   Instance 1    │ ◄── User A uploads image.png                     │
│  │   .files/       │                                                   │
│  │   └── image.png │                                                   │
│  └─────────────────┘                                                   │
│           ▲                                                            │
│           │         ┌─────────────────┐                                │
│           │         │   Instance 2    │ ◄── User B requests image.png │
│           │         │   .files/ = ∅   │ ──► 404 Not Found!           │
│           │         └─────────────────┘                                │
│           └── Load Balancer routes randomly                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Solution: PostgreSQL Storage

```
┌─────────────────────────────────────────────────────────────────────────┐
│  THE SOLUTION: PostgreSQL File Storage                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────┐     ┌────────────┐     ┌────────────────────────────┐  │
│  │ Instance 1 │     │ Instance 2 │     │         PostgreSQL         │  │
│  │            │     │            │     │  ┌─────────────────────┐   │  │
│  │ (stateless)│ ◄─► │ (stateless)│ ◄─► │  │   chainlit_files    │   │  │
│  │            │     │            │     │  │   ├── image.png     │   │  │
│  └────────────┘     └────────────┘     │  │   └── document.pdf  │   │  │
│                                         │  └─────────────────────┘   │  │
│  ✅ Any instance can serve any file    └────────────────────────────┘  │
│  ✅ Containers can crash/restart freely                               │
│  ✅ Single backup captures everything                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Decision Record

| Aspect | `.files/` (Local) | PostgreSQL (Production) |
|--------|-------------------|-------------------------|
| **Deployment** | ❌ Local/dev only | ✅ Cloud-ready |
| **Container restarts** | ❌ Files lost | ✅ Files persist |
| **Load balancing** | ❌ Instance-specific | ✅ Any instance |
| **Backups** | ❌ Separate process | ✅ Single `pg_dump` |
| **ACID compliance** | ❌ No transactions | ✅ Transactional |
| **Data sovereignty** | ❌ File system | ✅ Database |

### Implementation

We use Chainlit's **pluggable architecture** — this is the intended way:

```python
# Chainlit provides:
from chainlit.data.storage_clients.base import BaseStorageClient

# We implement:
class PostgresStorageClient(BaseStorageClient):
    """Stores files as BYTEA in PostgreSQL."""

    async def upload_file(self, object_key: str, data: bytes, ...) -> dict:
        # INSERT INTO chainlit_files ...

    async def get_read_url(self, object_key: str) -> str:
        # SELECT data FROM chainlit_files WHERE ...
```

*   **Implementation**: [`storage_postgres.py`](file:///c:/Users/rjjaf/_Projects/yonja/demo-ui/storage_postgres.py)
*   **Config**: [`.chainlitignore`](file:///c:/Users/rjjaf/_Projects/yonja/demo-ui/.chainlitignore) disables local storage

> [!TIP]
> **Twelve-Factor App Compliance**: This architecture follows principle #6 (Stateless Processes).
> See: https://12factor.net/processes

## ⚙️ Feature Configuration

To reduce UI noise for farmers, we specifically configure features in [.chainlit/config.toml](../../demo-ui/.chainlit/config.toml):

| Feature | Status | Reason |
|---------|--------|--------|
| `favorites` | ❌ Disabled | Reduces button clutter |
| `features.mcp` | ❌ Disabled | MCP is handled via backend logic, not UI plugins |
| `prompt_playground` | ❌ Disabled | Developer tool, not for end-users |
| `latex` | ❌ Disabled | Not needed for agricultural advice |
| `unsafe_allow_html` | ✅ Enabled | Required for AI-generated dashboard cards |
| `features.audio` | ✅ Enabled | Critical for voice input (accessibility) |

---

## 🔒 Security Notes

### OAuth Configuration
[oauth.json](../../demo-ui/.chainlit/oauth.json) contains **only scopes**, not secrets:
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
[config.toml](../../demo-ui/.chainlit/config.toml) restricts uploads to:
```toml
accept = ["image/*", "application/pdf"]  # No executables
max_files = 10
max_size_mb = 100
```

---

## 🚀 Running the App

### From VS Code (Recommended)
Run task: **🌿 ALİM: 🚀 Start All**

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
- [PostgreSQL File Storage](../../demo-ui/storage_postgres.py)
- [Chainlit Configuration Reference](https://docs.chainlit.io/configuration)
- [OAuth Setup Guide](11-CHAINLIT-UI.md)
- [chainlit-ui-ux.md](../../.agent/rules/chainlit-ui-ux.md) — **Agent rules for UI/UX code**

---

**Last Updated:** January 24, 2026
**Maintained By:** ZekaLab Team
