# Observability & Privacy Rules

> **Status**: ACTIVE
> **Scope**: Application-Wide (UI, API, Agent)
> **Compliance**: MANDATORY

## 1. Local Sovereignty (Data Residency)
*   **Local Execution**: All observability traces (Langfuse) and state checkpoints (LangGraph) MUST be processed locally or within the self-hosted infrastructure.
*   **No External Cloud**: Do NOT send traces to public cloud endpoints unless explicitly configured for a "Cloud" deployment tier.
*   **Containerization**: Ensure `langfuse-server` and `postgres` are reachable via the internal Docker network or `localhost`.

## 2. PII Masking (Zero-Trust Privacy)
*   **Entry Point Scrubbing**: All user input MUST pass through the `PIIMaskingNode` *before* reaching the LLM or being logged to the active trace.
*   **Gateway Usage**: Use `src/alim/security/pii_gateway.py` as the standard regex engine.
*   **Forbidden Data**: The following MUST be masked with placeholders (e.g., `[FİN]`, `[TELEFON]`):
    *   Azerbaijani FIN Codes (7 char)
    *   Phone Numbers (+994...)
    *   Email Addresses
    *   IBANs
    *   Exact GPS Coordinates (fuzzed or masked)

## 3. Feedback Loop
*   **Trace Linking**: Every user feedback event (👍/👎) MUST be linked to a specific Langfuse `trace_id`.
*   **Session Tagging**:
    *   `user_id`: Actual authenticated ID (or "anonymous").
    *   `tags`: `["production", "ALEM-v1", "direct_mode" | "http_mode"]`.

## 4. Hybrid Execution Model
*   **Direct Mode (Default)**: Use for production performance and reliability. Runs the agent graph in the same process as the UI/API.
*   **HTTP Mode**: Use for scaling/distributed setups.
*   **Toggle**: The system must support switching modes via configuration (`INTEGRATION_MODE`).
