# 🗄️ Storage Strategy: PostgreSQL vs. Local Files

## 🚫 The Anti-Pattern: Local `.files/`
Chainlit's default behavior is to store uploaded files and generated assets in a local `.files/` directory.

**Why we DISABLED this:**
1.  **Statelessness**: It violates 12-factor app principles (Factor VI). Containers should be stateless.
2.  **Scalability**: If we run multiple replicas of the UI, local files are not shared.
3.  **Persistence**: Files are lost if the container/pod is recreated.
4.  **Backup**: It is harder to backup a scattered filesystem than a centralized database.

## ✅ The Solution: PostgreSQL BLOB Storage
We have implemented a custom `PostgresStorage` client that overrides Chainlit's default file handling.

### Implementation Details
*   **Class**: `PostgresStorage` (in `demo-ui/storage_postgres.py`)
*   **Mechanism**:
    *   Intercepts file upload/persist calls.
    *   Stores binary data directly in the PostgreSQL `elements` table (or a dedicated `storage` table if configured) as `BYTEA` or via large object references.
    *   *Note: Ensure the implementation details match `demo-ui/storage_postgres.py`.*

### Configuration
To enforce this, the Chainlit configuration (`.chainlit/config.toml`) MUST NOT use local storage options, and the application MUST retrieve the storage client from our custom provider.

## ⚠️ Critical Rule
**Do not enable or rely on `demo-ui/.files/`.** This folder should be `.gitignore`d and considered ephemeral/empty. All persistence must go through the Database Layer.
