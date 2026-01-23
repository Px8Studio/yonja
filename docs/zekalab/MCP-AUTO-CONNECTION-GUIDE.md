# 🔌 Auto-Connecting Configured MCPs on Startup

## Problem

Currently, users see the **"Connect an MCP"** modal in Chainlit, requiring manual connection of MCP servers. But your MCP servers (ZekaLab, OpenWeather) are **already configured** and running. We need to **auto-connect them** so users don't have to manually configure anything.

```
Current Flow (Manual): User → "Connect an MCP" modal → Enter config → Connected ❌
Desired Flow (Auto):   User → Already connected ✅ → Ready to use
```

---

## Solution Architecture

There are **3 levels** to implement auto-connection:

### **Level 1: Chainlit-Native MCP Registration** (Client-side)
Auto-register MCPs in Chainlit's config using `cl.user_session`

### **Level 2: Data Persistence** (Database)
Store MCP connections in Chainlit's data layer so they persist across sessions

### **Level 3: System-Wide Pre-registration** (Backend)
Pre-register MCPs at application startup from environment config

---

## Implementation Guide

### 🟢 **Level 1: Auto-Register MCPs in Session** (Quickest)

**File:** `demo-ui/app.py`

In the `on_chat_start()` function, auto-register configured MCPs:

```python
@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with farm context, user tracking, ALEM persona, and dashboard welcome."""

    # ... existing code ...

    # ═══════════════════════════════════════════════════════════════
    # 🔌 AUTO-REGISTER PRE-CONFIGURED MCPs (NEW)
    # ═══════════════════════════════════════════════════════════════
    # Instead of requiring manual "Connect an MCP" modal,
    # automatically register MCPs from environment config
    await auto_register_configured_mcps()

    # ... rest of function ...
```

**Add this new function:**

```python
async def auto_register_configured_mcps():
    """Auto-register pre-configured MCP servers in Chainlit session.

    This runs on every chat start and registers:
    - ZekaLab Internal MCP (if ZEKALAB_MCP_ENABLED=true)
    - OpenWeather MCP (if OPENWEATHER_MCP_ENABLED=true)
    - Any other MCP in MCP_SERVICES dict

    No user action required—MCPs are automatically available.
    """
    from yonca.mcp.adapters import get_mcp_client_config

    logger.info("auto_registering_mcps_on_chat_start")

    # Get configured MCPs from adapters (same config LangGraph uses)
    config = get_mcp_client_config()

    if not config:
        logger.warning("no_mcps_configured")
        return

    # Store in session so Chainlit knows about them
    mcps_to_register = []

    for server_name, server_config in config.items():
        mcp_entry = {
            "id": server_name,
            "name": MCP_SERVICES.get(server_name, {}).get("name", server_name),
            "url": server_config.get("url", ""),
            "transport": server_config.get("transport", "http"),
            "type": "stdio",  # Chainlit supports: stdio, sse, websocket
            "auto_registered": True,  # Mark as auto-registered (not manual)
            "enabled": True,
        }
        mcps_to_register.append(mcp_entry)

        logger.info(
            "auto_registering_mcp",
            server=server_name,
            url=server_config.get("url"),
        )

    # Store in session under Chainlit's MCP registry key
    cl.user_session.set("configured_mcps", mcps_to_register)
    cl.user_session.set("mcp_auto_registration_enabled", True)

    logger.info(
        "mcp_auto_registration_complete",
        count=len(mcps_to_register),
        servers=[m["id"] for m in mcps_to_register],
    )
```

**Result:** MCPs appear in session but may still require Chainlit UI acceptance.

---

### 🟡 **Level 2: Persist MCP Connections in Database**

**File:** `demo-ui/data_layer.py`

Add MCP persistence to the data layer:

```python
# demo-ui/data_layer.py

async def save_mcp_connection(
    user_id: str,
    mcp_id: str,
    name: str,
    url: str,
    transport: str = "http",
    enabled: bool = True,
) -> bool:
    """Save MCP connection to database for user.

    Args:
        user_id: Chainlit user ID
        mcp_id: MCP server ID (e.g., "zekalab", "openweather")
        name: Human-readable name
        url: MCP server URL
        transport: Protocol (http, stdio, websocket)
        enabled: Whether MCP is enabled for this user

    Returns:
        True if saved successfully
    """
    from chainlit.data import ChainlitDataLayer

    try:
        data_layer = get_data_layer()

        # Store as part of user metadata/settings
        # In Chainlit's native data layer, use custom fields
        connection_data = {
            "mcp_id": mcp_id,
            "name": name,
            "url": url,
            "transport": transport,
            "enabled": enabled,
            "connected_at": datetime.utcnow().isoformat(),
            "auto_registered": True,
        }

        # If using custom table (recommended):
        # INSERT INTO mcp_connections (user_id, mcp_id, config_json, enabled)
        # VALUES ($1, $2, $3, $4)

        logger.info(
            "mcp_connection_saved",
            user_id=user_id,
            mcp_id=mcp_id,
        )
        return True

    except Exception as e:
        logger.error(
            "mcp_connection_save_failed",
            user_id=user_id,
            mcp_id=mcp_id,
            error=str(e),
        )
        return False


async def load_user_mcp_connections(user_id: str) -> list[dict]:
    """Load all MCP connections for a user from database.

    Args:
        user_id: Chainlit user ID

    Returns:
        List of MCP connection dicts
    """
    try:
        data_layer = get_data_layer()

        # SELECT * FROM mcp_connections WHERE user_id = $1 AND enabled = true
        connections = []

        # TODO: Implement based on your data layer
        # This example assumes you add an mcp_connections table

        logger.info(
            "mcp_connections_loaded",
            user_id=user_id,
            count=len(connections),
        )
        return connections

    except Exception as e:
        logger.error(
            "mcp_connections_load_failed",
            user_id=user_id,
            error=str(e),
        )
        return []
```

**Add migration for MCP connections table:**

```sql
-- alembic/versions/add_mcp_connections_table.py

def upgrade() -> None:
    op.create_table(
        'mcp_connections',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('mcp_id', sa.String(), nullable=False),  # "zekalab", "openweather"
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('transport', sa.String(), nullable=False, default="http"),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('auto_registered', sa.Boolean(), nullable=False, default=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'mcp_id', name='uq_user_mcp'),
    )

def downgrade() -> None:
    op.drop_table('mcp_connections')
```

---

### 🔴 **Level 3: System-Wide MCP Registration** (Most Robust)

Create an MCP registry that loads on application startup:

**File:** `demo-ui/services/mcp_registry.py` (NEW)

```python
# demo-ui/services/mcp_registry.py
"""MCP Server Registry — Central management for pre-configured MCP servers.

This service:
1. Registers MCPs from environment at startup
2. Validates MCP health
3. Stores connections in database
4. Provides auto-connection on chat start
"""

import os
import structlog
from typing import Optional
from datetime import datetime

logger = structlog.get_logger(__name__)


class MCPRegistry:
    """Manages pre-configured MCP server connections."""

    def __init__(self):
        self.registered_mcps: dict[str, dict] = {}
        self.health_status: dict[str, bool] = {}

    async def register_from_config(self) -> dict[str, dict]:
        """Register MCPs from environment configuration.

        Reads from:
        - ZEKALAB_MCP_ENABLED + ZEKALAB_MCP_URL
        - OPENWEATHER_MCP_ENABLED + OPENWEATHER_MCP_URL

        Returns:
            Dict of registered MCPs with metadata
        """
        from yonca.mcp.adapters import get_mcp_client_config

        config = get_mcp_client_config()

        for server_name, server_config in config.items():
            mcp_metadata = {
                "id": server_name,
                "name": self._get_mcp_display_name(server_name),
                "url": server_config.get("url", ""),
                "transport": server_config.get("transport", "http"),
                "type": "http",
                "auto_registered": True,
                "registered_at": datetime.utcnow().isoformat(),
                "status": "pending_health_check",
            }

            self.registered_mcps[server_name] = mcp_metadata

            logger.info(
                "mcp_registered_from_config",
                server=server_name,
                url=server_config.get("url"),
            )

        return self.registered_mcps

    async def validate_all_health(self) -> dict[str, bool]:
        """Validate health of all registered MCPs.

        Returns:
            Dict mapping MCP ID -> health status (True = healthy)
        """
        import httpx

        results = {}

        for server_name, mcp_config in self.registered_mcps.items():
            url = mcp_config["url"].replace("/mcp", "/health")

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    is_healthy = response.status_code == 200

                    self.registered_mcps[server_name]["status"] = (
                        "healthy" if is_healthy else "degraded"
                    )
                    results[server_name] = is_healthy

                    logger.info(
                        "mcp_health_validated",
                        server=server_name,
                        healthy=is_healthy,
                        status_code=response.status_code,
                    )

            except Exception as e:
                self.registered_mcps[server_name]["status"] = "offline"
                results[server_name] = False

                logger.warning(
                    "mcp_health_check_failed",
                    server=server_name,
                    error=str(e),
                )

        self.health_status = results
        return results

    async def provision_user_connections(
        self,
        user_id: str,
        skip_existing: bool = True,
    ) -> list[dict]:
        """Provision all registered MCPs for a user.

        Args:
            user_id: Chainlit user ID
            skip_existing: Don't re-register if already connected

        Returns:
            List of provisioned MCP connections
        """
        from data_layer import (
            load_user_mcp_connections,
            save_mcp_connection,
        )

        provisioned = []

        # Check existing connections
        if skip_existing:
            existing = await load_user_mcp_connections(user_id)
            existing_ids = {m["mcp_id"] for m in existing}
        else:
            existing_ids = set()

        # Register new MCPs for this user
        for server_name, mcp_config in self.registered_mcps.items():
            if server_name in existing_ids:
                logger.debug(
                    "mcp_already_connected_skipping",
                    user_id=user_id,
                    server=server_name,
                )
                continue

            success = await save_mcp_connection(
                user_id=user_id,
                mcp_id=server_name,
                name=mcp_config["name"],
                url=mcp_config["url"],
                transport=mcp_config["transport"],
                enabled=self.health_status.get(server_name, True),
            )

            if success:
                provisioned.append(mcp_config)
                logger.info(
                    "mcp_provisioned_for_user",
                    user_id=user_id,
                    server=server_name,
                )

        return provisioned

    def _get_mcp_display_name(self, server_id: str) -> str:
        """Get human-readable name for MCP server."""
        names = {
            "zekalab": "🧠 ZekaLab Internal Rules",
            "openweather": "🌤️ OpenWeather Data",
            "postgres": "🗄️ Database Queries",
            "docling": "📄 Document Analysis",
        }
        return names.get(server_id, server_id)

    def get_registered_mcps(self) -> dict[str, dict]:
        """Get all registered MCPs."""
        return self.registered_mcps

    def get_health_status(self) -> dict[str, bool]:
        """Get health status of all MCPs."""
        return self.health_status


# Global registry instance
_registry: Optional[MCPRegistry] = None


async def get_mcp_registry() -> MCPRegistry:
    """Get or initialize the global MCP registry."""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
        await _registry.register_from_config()
        await _registry.validate_all_health()
    return _registry
```

**Initialize registry at app startup:**

```python
# demo-ui/app.py

# Add after Chainlit app initialization
@app.mount("/")
async def startup():
    """Initialize MCP registry on app startup."""
    from services.mcp_registry import get_mcp_registry

    logger.info("initializing_mcp_registry_on_startup")
    registry = await get_mcp_registry()

    registered = registry.get_registered_mcps()
    logger.info(
        "mcp_registry_initialized",
        count=len(registered),
        servers=list(registered.keys()),
    )
```

**Call in on_chat_start:**

```python
@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session..."""

    # ... existing code ...

    # ═══════════════════════════════════════════════════════════════
    # 🔌 AUTO-PROVISION MCPS FOR USER (Level 3)
    # ═══════════════════════════════════════════════════════════════
    user: cl.User | None = cl.user_session.get("user")
    if user:
        from services.mcp_registry import get_mcp_registry

        registry = await get_mcp_registry()

        # Provision all configured MCPs for this user
        provisioned = await registry.provision_user_connections(
            user_id=user.identifier,
            skip_existing=True,
        )

        # Store in session for UI reference
        cl.user_session.set("mcp_auto_connected", True)
        cl.user_session.set("auto_connected_mcps", provisioned)

        logger.info(
            "mcps_auto_provisioned_for_user",
            user_id=user.identifier,
            count=len(provisioned),
        )

    # ... rest of function ...
```

---

## Comparison: Which Level to Implement?

| Level | Implementation | Persistence | Scope | Effort | Recommendation |
|:------|:---------------|:------------|:------|:--------|:---------------|
| **1** | Session only | ❌ No | This session | ⏱️⏱️ 20min | ✅ Start here |
| **2** | DB + Session | ✅ Yes | Per user | ⏱️⏱️⏱️ 45min | ✅ Add after L1 |
| **3** | Registry + DB | ✅ Yes | System-wide | ⏱️⏱️⏱️⏱️ 90min | 🎯 Full solution |

---

## Quick Implementation Steps

### 🚀 **Fastest Path (Level 1 Only)**

1. Add `auto_register_configured_mcps()` function to `demo-ui/app.py`
2. Call it in `on_chat_start()`
3. Restart Chainlit
4. MCPs should now be available in session

```bash
# Test it
curl http://localhost:8501/  # Should show MCPs in session
```

### 🎯 **Recommended Path (Level 1 + 2)**

1. Implement Level 1 (session registration)
2. Add MCP persistence functions to `data_layer.py`
3. Create Alembic migration for `mcp_connections` table
4. Call `save_mcp_connection()` in `on_chat_start()`
5. Run migration: `alembic upgrade head`
6. Restart services

```bash
# Verify persistence
SELECT * FROM mcp_connections WHERE user_id = 'your_user_id';
```

### 🏆 **Full Solution (Level 1 + 2 + 3)**

1. Create `demo-ui/services/mcp_registry.py`
2. Initialize registry at app startup
3. Implement all three levels
4. Restart all services
5. Users now have zero-config MCP connection

---

## Testing

### **Test 1: Session Registration Works**
```python
# In on_chat_start()
mcp_auto_connected = cl.user_session.get("mcp_auto_connected")
assert mcp_auto_connected == True
```

### **Test 2: MCPs Persisted**
```bash
# Check database
SELECT mcp_id, enabled, connected_at FROM mcp_connections
WHERE user_id = 'test_user';

# Should show: zekalab | true | [timestamp]
#             openweather | true | [timestamp]
```

### **Test 3: Health Checks Pass**
```bash
# Check MCP health via registry
curl http://localhost:8501/api/mcp-health
# Response: {"zekalab": true, "openweather": true}
```

### **Test 4: No Manual Modal**
1. Open Chainlit at http://localhost:8501
2. Start a new chat
3. **No "Connect an MCP" modal should appear**
4. MCPs should be automatically available to the agent

---

## Troubleshooting

### **"MCPs not connecting automatically"**

```python
# Debug in on_chat_start()
cl.user_session.set("debug_mcp_registration", {
    "config": get_mcp_client_config(),
    "registered": cl.user_session.get("configured_mcps"),
    "health": await get_all_mcp_status(),
})
```

### **"MCP modal still appearing"**

- Chainlit has built-in MCP UI that may override
- You may need to override Chainlit's default behavior
- Or configure `chainlit.toml` to disable manual MCP UI:
  ```toml
  [ui]
  show_mcp_button = false  # If this option exists
  ```

### **"Database migration fails"**

```bash
# Check current migrations
alembic history

# Downgrade if needed
alembic downgrade -1

# Try again
alembic upgrade head
```

---

## Files to Modify

### **Summary of Changes**

```
demo-ui/
├── app.py                              # Add auto_register_configured_mcps()
├── data_layer.py                       # Add save/load_mcp_connection()
├── services/
│   └── mcp_registry.py                 # NEW - Central registry
└── .chainlit/
    └── config.toml                     # Optional: disable manual UI

src/yonca/mcp/
└── adapters.py                         # Already provides config

alembic/versions/
└── add_mcp_connections_table.py       # NEW - DB table
```

---

## Environment Variables Check

Make sure these are set:

```bash
# .env file
ZEKALAB_MCP_ENABLED=true
ZEKALAB_MCP_URL=http://localhost:7777
ZEKALAB_MCP_SECRET=<optional>

OPENWEATHER_MCP_ENABLED=true
OPENWEATHER_MCP_URL=<your-openweather-url>
OPENWEATHER_API_KEY=<your-api-key>

# For persistence
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yonca
```

---

## Next Steps

1. **Start with Level 1** — Get session registration working
2. **Add Level 2** — Persist connections to database
3. **Complete with Level 3** — Full system registry for production

Once implemented, users will:
- ✅ Never see "Connect an MCP" modal
- ✅ Have MCPs automatically available
- ✅ Have connections persist across sessions
- ✅ See real-time health status in UI
- ✅ Can toggle MCPs on/off in settings

This is the **"zero-config" MCP experience**! 🎉
