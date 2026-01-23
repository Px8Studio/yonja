# 🗄️ Chainlit Database Schema — Architectural Rules

> **Purpose:** Enforce Chainlit's required table structure and understand non-negotiable constraints
> **Status:** Production schema documented with enforcement rules
> **Updated:** 2026-01-21

---

## 🚨 Critical Understanding

### Chainlit Tables Are NON-NEGOTIABLE

**Yes, Chainlit enforces a strict schema.** These tables MUST exist with EXACT column names and types:

```
┌─────────────────────────────────────────────────────────────┐
│           CHAINLIT REQUIRED TABLES (5 Core)                  │
├─────────────────────────────────────────────────────────────┤
│  1. users        → OAuth identity                            │
│  2. threads      → Conversation sessions                     │
│  3. steps        → Individual messages                       │
│  4. elements     → File attachments (images, PDFs)           │
│  5. feedbacks    → User reactions (👍/👎)                     │
└─────────────────────────────────────────────────────────────┘
```

**Source:** Chainlit's SQLAlchemyDataLayer expects these tables.
**Consequence:** If tables are missing or columns are wrong, Chainlit data persistence **breaks silently** or throws errors.

---

## 📋 The Official Schema (From Chainlit Source)

### 1. `users` Table

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,              -- UUID, NOT NULL
    identifier VARCHAR(255) NOT NULL UNIQUE, -- Email from OAuth, NOT NULL
    "createdAt" VARCHAR(30) NOT NULL,        -- ISO timestamp string, NOT NULL
    metadata TEXT                            -- JSON (chat_settings, etc)
);

CREATE UNIQUE INDEX ix_users_identifier ON users(identifier);
```

**Key Rules:**
- ❌ **Cannot rename columns** (e.g., `createdAt` must have capital `A`)
- ❌ **Cannot change types** (`createdAt` is VARCHAR, not TIMESTAMP)
- ✅ Can add custom columns (e.g., `last_login_at`) but don't touch core ones
- ✅ `metadata` is free-form JSON — store anything here

**Why VARCHAR for timestamps?**
- Chainlit uses ISO 8601 strings, not native TIMESTAMP
- Allows timezone-aware strings like `"2026-01-21T15:30:00.123Z"`

---

### 2. `threads` Table

```sql
CREATE TABLE threads (
    id VARCHAR(36) PRIMARY KEY,        -- UUID, NOT NULL
    "createdAt" VARCHAR(30),           -- ISO timestamp string
    name VARCHAR(255),                 -- Thread title/name
    "userId" VARCHAR(36),              -- FK to users.id
    "userIdentifier" VARCHAR(255),     -- Denormalized email
    tags TEXT,                         -- JSON array: ["profile:cotton", "region:lankaran"]
    metadata TEXT                      -- JSON: {farm_id, expertise_areas, etc}
);

CREATE INDEX ix_threads_userId ON threads("userId");
```

**Key Rules:**
- ❌ **Cannot rename `userId` or `userIdentifier`** (Chainlit expects these)
- ✅ `metadata` is YOUR space — store session state here
- ✅ `tags` is JSON array — use for filtering/searching threads
- ⚠️ `userIdentifier` is denormalized — Chainlit does this for performance

**What to store in `metadata`:**
```json
{
  "farm_id": "demo_farm_001",
  "expertise_areas": ["cotton", "advanced"],
  "alem_persona_fin": "4F7U713",
  "language": "az",
  "active_model": {"provider": "ollama", "model": "qwen3:4b"}
}
```

---

### 3. `steps` Table (Most Complex)

```sql
CREATE TABLE steps (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255),                  -- Step name (optional)
    type VARCHAR(50),                   -- "user_message", "assistant_message", "tool", etc
    "threadId" VARCHAR(36),             -- FK to threads.id
    "parentId" VARCHAR(36),             -- For nested steps
    streaming BOOLEAN,                  -- Whether step is streaming
    "waitForAnswer" BOOLEAN,            -- Whether waiting for user input
    "isError" BOOLEAN,                  -- Whether step failed
    metadata TEXT,                      -- JSON
    tags TEXT,                          -- JSON array
    input TEXT,                         -- User message or tool input
    output TEXT,                        -- AI response or tool output
    "createdAt" VARCHAR(30),            -- ISO timestamp
    "start" VARCHAR(30),                -- Execution start time
    "end" VARCHAR(30),                  -- Execution end time
    generation TEXT,                    -- JSON: {model, tokens, etc}
    "showInput" VARCHAR(10),            -- "true"/"false" string
    language VARCHAR(50),               -- Code language (for code blocks)
    "defaultOpen" BOOLEAN DEFAULT false -- Whether step is expanded by default
);

CREATE INDEX ix_steps_threadId ON steps("threadId");
```

**Key Rules:**
- ❌ **Column names are camelCase** (e.g., `threadId`, not `thread_id`)
- ❌ **Boolean columns are NULLABLE** (Chainlit doesn't set all of them)
- ✅ `generation` stores LLM metadata — use for model info
- ✅ `parentId` enables nested steps (future feature)

**Example `generation` JSON:**
```json
{
  "model": "ollama/qwen3:4b",
  "provider": "ollama",
  "tokenCount": 150,
  "promptTokens": 50,
  "completionTokens": 100,
  "latencyMs": 1200
}
```

---

### 4. `elements` Table

```sql
CREATE TABLE elements (
    id VARCHAR(36) PRIMARY KEY,
    "threadId" VARCHAR(36),        -- FK to threads.id
    type VARCHAR(50),              -- "image", "file", "pdf", "video", etc
    "chainlitKey" VARCHAR(255),    -- Chainlit internal key
    url TEXT,                      -- Public URL or data URI
    "objectKey" VARCHAR(500),      -- S3/storage key
    name VARCHAR(255),             -- Filename
    display VARCHAR(50),           -- "inline", "side", "page"
    size VARCHAR(50),              -- File size string
    language VARCHAR(50),          -- Code language
    page INTEGER,                  -- PDF page number
    "autoPlay" BOOLEAN,            -- Media auto-play
    "playerConfig" TEXT,           -- JSON player config
    "forId" VARCHAR(36),           -- Step ID this element belongs to
    mime VARCHAR(100),             -- MIME type
    props TEXT                     -- JSON additional properties
);

CREATE INDEX ix_elements_threadId ON elements("threadId");
CREATE INDEX ix_elements_forId ON elements("forId");
```

**Key Rules:**
- ❌ **Must have both `threadId` and `forId`** (dual indexing)
- ✅ `url` can be data URI (e.g., `data:image/png;base64,...`)
- ✅ Use `objectKey` for cloud storage integration (S3, Azure Blob)

---

### 5. `feedbacks` Table

```sql
CREATE TABLE feedbacks (
    id VARCHAR(36) PRIMARY KEY,
    "forId" VARCHAR(36),       -- Step ID this feedback is for
    "threadId" VARCHAR(36),    -- Thread ID
    value INTEGER,             -- 1 = positive, -1 = negative
    comment TEXT               -- Optional user comment
);

CREATE INDEX ix_feedbacks_forId ON feedbacks("forId");
```

**Key Rules:**
- ❌ **`value` is INTEGER, not BOOLEAN** (allows future multi-level ratings)
- ✅ `comment` is optional — users can explain their feedback

---

## 🗄️ Where Are These Tables Stored?

### Current Setup

```
📍 Location: PostgreSQL Database
   Host: localhost:5433
   Database: yonca
   User: yonca
   Password: yonca_dev_password

Tables:
├── Domain Tables (Your Business Logic)
│   ├── user_profiles
│   ├── farms
│   ├── parcels
│   ├── alem_personas
│   └── ...
│
└── Chainlit Tables (UI Persistence) ✅
    ├── users
    ├── threads
    ├── steps
    ├── elements
    └── feedbacks
```

**Created by:** [alembic/versions/add_chainlit_data_layer_tables.py](alembic/versions/add_chainlit_data_layer_tables.py)

**Migration Status:**
```bash
# Check if tables exist
cd c:\Users\rjjaf\_Projects\yonja
.\.venv\Scripts\alembic.exe history

# Apply if not created
.\.venv\Scripts\alembic.exe upgrade head
```

---

## 🚨 Hard Architectural Rules

### Rule 1: DO NOT Modify Chainlit Table Structure

```python
# ❌ WRONG - Breaking Chainlit expectations
ALTER TABLE users RENAME COLUMN "createdAt" TO created_at;
ALTER TABLE threads ALTER COLUMN metadata TYPE jsonb;
ALTER TABLE steps DROP COLUMN "waitForAnswer";

# ✅ CORRECT - Add to YOUR domain tables
ALTER TABLE user_profiles ADD COLUMN preferences jsonb;
ALTER TABLE farms ADD COLUMN geolocation point;
```

**Why?**
- Chainlit's ORM expects exact column names
- Breaking this causes silent failures or exceptions
- Chainlit updates may add columns — don't conflict

---

### Rule 2: Separate Concerns (Chainlit vs Domain)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CHAINLIT TABLES (UI State)          DOMAIN TABLES (Business)│
│  ────────────────────────            ─────────────────────── │
│  • users → OAuth identity             • user_profiles → Real│
│  • threads → UI conversations         • farms → Real farms  │
│  • steps → Chat messages              • parcels → Real land │
│  • elements → Attachments             • alem_personas →     │
│  • feedbacks → Reactions              •   Synthetic farmers │
│                                                              │
│  Link via:                            Link via:             │
│  users.id ──FK──▶ alem_personas.chainlit_user_id           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Pattern:**
- Chainlit tables = Presentation layer (what user sees in UI)
- Domain tables = Business layer (actual farm data, logic)
- Link via foreign keys but **don't merge schemas**

---

### Rule 3: Use `metadata` JSON Fields for Extensions

```python
# ✅ CORRECT - Extend via metadata
thread.metadata = {
    "farm_id": "F123",
    "expertise_areas": ["cotton"],
    "custom_field": "value",
    "your_app_data": {...}
}

# ❌ WRONG - Add columns to Chainlit tables
ALTER TABLE threads ADD COLUMN farm_id VARCHAR(20);
ALTER TABLE threads ADD COLUMN expertise_areas TEXT[];
```

**Why?**
- Chainlit migrations won't conflict with your data
- Easy to version (change JSON structure, not schema)
- Future-proof for Chainlit updates

---

### Rule 4: Index Foreign Keys (Performance)

```sql
-- ✅ Already done in migration
CREATE INDEX ix_threads_userId ON threads("userId");
CREATE INDEX ix_steps_threadId ON steps("threadId");
CREATE INDEX ix_elements_threadId ON elements("threadId");
CREATE INDEX ix_elements_forId ON elements("forId");
CREATE INDEX ix_feedbacks_forId ON feedbacks("forId");

-- ✅ Add for your domain tables
CREATE INDEX ix_alem_personas_chainlit_user_id ON alem_personas(chainlit_user_id);
CREATE INDEX ix_user_profiles_email ON user_profiles(email);
```

---

## 🔐 Enforcement Strategies

### Strategy 1: Alembic Migration Lock

```python
# alembic/versions/add_chainlit_data_layer_tables.py

"""Add Chainlit data layer tables for user/thread/step persistence

⚠️ WARNING: DO NOT MODIFY THIS MIGRATION
These tables are required by Chainlit's SQLAlchemyDataLayer.
Changing column names or types will break Chainlit persistence.

If you need custom fields:
1. Add them to metadata JSON columns (threads.metadata, etc)
2. Create separate domain tables (user_profiles, farms, etc)
3. Link via foreign keys (e.g., alem_personas.chainlit_user_id → users.id)
"""

def upgrade() -> None:
    """Create Chainlit data layer tables."""
    # ... (current code)
```

---

### Strategy 2: Database Migration Comments

```sql
-- In your migration files, add warnings:

COMMENT ON TABLE users IS 'Chainlit OAuth users - DO NOT MODIFY SCHEMA';
COMMENT ON TABLE threads IS 'Chainlit conversation threads - DO NOT MODIFY SCHEMA';
COMMENT ON TABLE steps IS 'Chainlit message steps - DO NOT MODIFY SCHEMA';
COMMENT ON TABLE elements IS 'Chainlit file attachments - DO NOT MODIFY SCHEMA';
COMMENT ON TABLE feedbacks IS 'Chainlit user feedback - DO NOT MODIFY SCHEMA';
```

---

### Strategy 3: Database Check Constraint

```sql
-- Add to migration to prevent accidental column removal
ALTER TABLE users ADD CONSTRAINT check_chainlit_users_schema
    CHECK (
        pg_catalog.pg_get_constraintdef(
            (SELECT oid FROM pg_constraint WHERE conname = 'users_pkey')
        ) IS NOT NULL
    );
```

---

### Strategy 4: Documentation + Code Review

1. **Add to ARCHITECTURE.md:**
   ```markdown
   ## Database Schema Rules

   ### ❌ NEVER MODIFY
   - Chainlit tables: users, threads, steps, elements, feedbacks
   - Column names (camelCase like `userId`, `createdAt`)
   - Column types (VARCHAR for timestamps, TEXT for JSON)

   ### ✅ ALWAYS DO
   - Use metadata JSON fields for extensions
   - Create separate domain tables for business logic
   - Link via foreign keys (chainlit_user_id → users.id)
   ```

2. **Add pre-commit hook:**
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash

   # Check if migration modifies Chainlit tables
   if git diff --cached --name-only | grep -q "alembic/versions/add_chainlit"; then
       echo "❌ ERROR: Cannot modify Chainlit data layer migration!"
       echo "   Create a NEW migration instead."
       exit 1
   fi
   ```

---

## 📚 What Else Is Non-Negotiable?

### 1. OAuth Callback URL Format

```python
# Chainlit expects this EXACT URL pattern:
# http://localhost:8501/auth/oauth/{provider}/callback

# ❌ Cannot change to:
# http://localhost:8501/oauth/callback
# http://localhost:8501/login/google
```

### 2. Session Storage Key Names

```python
# Chainlit uses these session keys internally:
cl.user_session.get("id")         # Session ID (UUID)
cl.user_session.get("user")       # Authenticated user (cl.User)
cl.user_session.get("chat_profile") # Active profile name

# ✅ Your custom keys:
cl.user_session.set("farm_id", "F123")
cl.user_session.set("alem_persona", {...})
```

### 3. Data Layer Registration

```python
# Must use this EXACT decorator:
@cl.data_layer
def _get_data_layer():
    return YoncaDataLayer(conninfo=db_url)

# ❌ Cannot use custom names:
@cl.my_data_layer  # Won't work
```

### 4. Element Types

```python
# Chainlit recognizes these element types:
- "image"
- "file"
- "pdf"
- "video"
- "audio"
- "text"
- "plotly"
- "avatar"

# ❌ Custom types won't render properly in UI
```

---

## 🎯 Summary

### Non-Negotiable (From Chainlit)

| Component | Rule | Reason |
|-----------|------|--------|
| **Table names** | Must be `users`, `threads`, `steps`, etc | Hardcoded in Chainlit ORM |
| **Column names** | Must be camelCase (`userId`, not `user_id`) | Chainlit expects exact names |
| **Column types** | VARCHAR for timestamps, TEXT for JSON | Chainlit serialization format |
| **Indexes** | Must have FK indexes on `userId`, `threadId`, etc | Performance requirements |

### Your Freedom

| What You Can Do | How |
|----------------|-----|
| Add custom fields | Use `metadata` JSON columns |
| Store business data | Create separate domain tables |
| Link data | Foreign keys: `alem_personas.chainlit_user_id → users.id` |
| Index optimization | Add indexes on your domain tables |

---

## 🛡️ Checklist for New Developers

Before modifying database:

- [ ] Is this a Chainlit table? → **DO NOT MODIFY**
- [ ] Do I need custom data? → **Use `metadata` JSON or create domain table**
- [ ] Am I changing column names? → **STOP! Create new domain table instead**
- [ ] Am I adding indexes? → **OK if on domain tables, check Chainlit tables first**
- [ ] Am I changing data types? → **NEVER on Chainlit tables**

---

**Remember:** Chainlit tables are like a third-party library's database — you don't modify the library's internals, you extend around it.
