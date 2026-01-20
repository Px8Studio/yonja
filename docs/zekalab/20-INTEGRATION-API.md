# 🌐 Yonca AI — Integration API Quickstart

> Purpose: Make the integration path crystal clear for Yonca Mobile and partners — which server to call, how requests flow, and minimal examples to test end‑to‑end.

---

## 🧭 Which Server Does Yonca Mobile Call?

- Primary entry point: FastAPI backend (:8000). This is the production API Yonca Mobile should integrate with.
- LangGraph Dev Server (:2024): Optional developer tool for visual debugging; not an integration target.
- Chainlit Demo UI (:8501): Demo/chat interface for showcasing ALEM; not used by Yonca Mobile.

---

## 🔁 Request Flow Overview

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart LR
    mobile["📱 Yonca Mobile<br/><i>Client</i>"]
    api["🧩 FastAPI Backend<br/><i>Port 8000</i>"]
    graphlib["🧠 LangGraph Library<br/><i>Agent orchestration</i>"]
    redis[(🧰 Redis<br/><i>Checkpoints</i>)]
    db[(🗄️ Yonca App DB<br/><i>PostgreSQL</i>)]
    langfuse[[📊 Langfuse<br/><i>Observability</i>]]
    studio["🎨 LangGraph Dev Server<br/><i>Port 2024</i>"]

    mobile -->|HTTPS REST| api
    api --> graphlib
    graphlib -->|state| redis
    api -->|read/write| db
    api -->|callbacks| langfuse
    studio -.->|optional visual debug| graphlib

    style api fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style graphlib fill:#fffde7,stroke:#f9a825
    style studio fill:#ede7f6,stroke:#7e57c2,stroke-dasharray: 4 4
    style langfuse fill:#f3e5f5,stroke:#7b1fa2
    style db fill:#e8f5e9,stroke:#2e7d32
    style redis fill:#e0f2f1,stroke:#00897b
```

Key points:
- Only the FastAPI backend is the external contract for Yonca Mobile.
- The LangGraph Dev Server is a developer tool; it does not expose production endpoints.

---

## 🚪 Standard Endpoints (Contract)

These endpoints provide full functionality for chat/agent, vision analysis, and data queries.

1. **POST `/api/v1/auth/test`** ⭐
   - Purpose: Verify authentication tokens and test integration setup.
   - Payload (minimal):
     ```json
     {
       "test_token": "optional"
     }
     ```
   - Headers:
     ```
     Authorization: Bearer <your_jwt_token>
     ```
   - Response (example):
     ```json
     {
       "authenticated": true,
       "token_valid": true,
       "user_id": "demo-user",
       "message": "✅ Authentication successful (dev mode)"
     }
     ```

2. **POST `/api/v1/chat`**
   - Purpose: Send a user message to ALEM and receive an actionable response.
   - Payload (minimal):
     ```json
     {
       "user_id": "uuid-or-session",
       "message": "Pomidorları nə vaxt suvarmalıyam?",
       "farm_id": "optional",
       "context": {"region_code": "ARAN"}
     }
     ```
   - Response (example):
     ```json
     {
       "short_answer": "Səhər və axşam suvarın.",
       "steps": ["Torpaq rütubətini yoxlayın", "Günorta suvarmadan çəkinin"],
       "risk": "LOW",
       "rule_refs": ["RULE_IRR_001"]
     }
     ```

3. **POST `/api/v1/vision/analyze`**
   - Purpose: Upload an image for crop/pest analysis.
   - Example:
     ```bash
     curl -X POST \
       -H "Authorization: Bearer <token>" \
       -F "file=@./leaf.jpg" \
       http://localhost:8000/api/v1/vision/analyze
     ```

4. **POST `/api/sql/query`** (experimental)
   - Purpose: NL-to-SQL + read-only execution for dashboards.
   - Payload:
     ```json
     { "query": "Show me farms with area > 50 hectares" }
     ```
   - Response: Markdown table with up to 1000 rows.

5. **GET `/health`**
   - Purpose: Health check (readiness/liveness).

6. **GET `/docs`**
   - Purpose: Swagger/OpenAPI UI for developer testing.

7. **GET `/`**
   - Purpose: API info and available endpoints.

Notes:
- Vision route is fully implemented at `/api/v1/vision/analyze`.
- Auth test route is live at `/api/v1/auth/test` for quick token verification.
- Chat route exists; ensure payload matches schema (see Swagger docs).

---

## 🔑 Authentication Modes

- Production: `Authorization: Bearer <JWT>` (SİMA/ASAN OIDC planned). Validate locally via public key or provider endpoint.
- Development (optional): `X-API-Key: <dev-key>` for rapid testing with synthetic data.

Environment hints:
- `DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@localhost:5433/yonca`
- Langfuse keys available via environment if observability is enabled.

---

## ⚡ Quick Test Examples

Auth test (verify tokens):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token_12345" \
  -d '{"test_token": "optional"}' \
  http://localhost:8000/api/v1/auth/test
```

Chat (JSON):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
        "user_id": "demo-user",
        "message": "Pomidorları nə vaxt suvarmalıyam?",
        "context": {"region_code": "ARAN"}
      }' \
  http://localhost:8000/api/v1/chat
```

Vision (file upload):
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@./leaf.jpg" \
  http://localhost:8000/api/v1/vision/analyze
```

SQL (read-only):
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "SELECT id, name, total_area_ha FROM farms WHERE total_area_ha > 50"}' \
  http://localhost:8000/api/sql/query
```

---

## 🧩 Positioning Guidance

- Sidecar OS: “ALEM inside Yonca” — we don’t touch EKTIS directly; we expose a clean REST contract that Yonca Mobile can call today.
- Hot‑swap ready: Synthetic data mirrors real schema; flipping to real sources requires no code changes at the API layer.
- Developer‑friendly: Swagger at :8000, optional dev API key, and clear examples reduce integration friction.
- Observability: Langfuse traces give confidence in reasoning quality and performance from day one.

Messaging to Yonca team:
- “Your app calls our FastAPI endpoints at :8000. Each request is orchestrated by LangGraph and fully traceable in Langfuse. You can test via Swagger immediately with synthetic data and switch to real sources later without changing your code.”

---

## 👀 Blind Spots to Watch

- Auth alignment: Finalize JWT/OIDC format (SİMA/ASAN) and public key distribution.
- Rate limits & quotas: Agree on per‑user and per‑tenant limits for production.
- Error contracts: Standardize error payloads (codes/messages) to match Yonca Mobile expectations.
- Versioning: Introduce `v1` path prefix and changelog for backward compatibility.
- Network security: Ensure TLS/HTTPS at the edge (Traefik/Nginx) before external exposure.

---

## 📎 References

- Architecture and roles: see [docs/zekalab/03-ARCHITECTURE.md](../03-ARCHITECTURE.md)
- Observability: see [docs/zekalab/07-OBSERVABILITY.md](../07-OBSERVABILITY.md)
- Advanced features (Vision, NL‑to‑SQL): see [docs/zekalab/16-ADVANCED-FEATURES.md](../16-ADVANCED-FEATURES.md)
