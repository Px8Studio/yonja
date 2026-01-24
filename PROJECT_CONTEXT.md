# Yonca AI - Project Context & Rules

## 🧠 Core Principles
1.  **12-Factor App**: Adhere strictly to 12-factor principles. Config in env, backing services attached resources, strict separation of build/release/run.
2.  **Quality Gates**: Always run `scripts/pre-start-checks.ps1` before committing.
3.  **Strict Architecture**:
    *   **Frontend**: Chainlit (Port 8501) - *Stateful UI, strictly following strict schema rules.*
    *   **Backend**: FastAPI (Port 8000) - *Stateless REST API.*
    *   **Logic**: ZekaLab MCP Server (Port 7777) - *Internal agricultural rules engine.*
    *   **Orchestration**: LangGraph (Port 2024).

## 🛠️ Tech Stack Rules
*   **Language**: Python 3.10+, strictly typed (`ruff` enforced).
*   **Web**: FastAPI for API, Chainlit for Chat UI.
*   **Data**: PostgreSQL (Persistence), Redis (Cache/Session).
*   **LLM**: Ollama (Local), Langfuse (Observability).
*   **Testing**: Pytest with `AsyncMock` for all IO-bound services.

## 🚨 Critical Constraints

### Database Schema (Non-Negotiable)
*   **Chainlit Tables** (`users`, `threads`, `steps`, `elements`, `feedbacks`) must **NEVER** be modified in structure (column names/types).
*   **Extensions**: Use the `metadata` JSON column for custom fields (e.g., `farm_id`, `expertise_areas`).
*   **Domain Data**: Store business logic in separate tables (`user_profiles`, `farms`).

### Storage Architecture
*   **No Local Files**: Use of `.files/` is **FORBIDDEN**.
*   **Persistence**: All file artifacts (images, PDFs) must be stored in PostgreSQL via `PostgresStorage`.


### Quality & Workflow
*   **Pre-Commit**: Ruff linting and formatting are enforced.
*   **MCP Integration**:
    *   Use **backend-managed connectors** (preloaded via `yonca.mcp.adapters`).
    *   Profile-based access: `agent` profile gets full tools; `fast`/`thinking` get none.
    *   Handling race conditions: Implement retry logic for MCP connections.

## 📂 Key Documentation Map
*   **Architecture**: `docs/ARCHITECTURE_ANALYSIS.md`
*   **DB Rules**: `docs/CHAINLIT_SCHEMA_RULES.md`
*   **MCP Info**: `docs/MCP-IMPLEMENTATION.md`
*   **Quality**: `docs/QUALITY-GATES.md`
*   **Storage**: `docs/STORAGE_STRATEGY.md`
