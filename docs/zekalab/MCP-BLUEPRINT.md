# MCP Blueprint — Sovereign AI Stack (2026)

**Date:** January 23, 2026
**Scope:** ALEM production architecture using LangGraph (captain) + FastMCP (crew) + Chainlit (window)

---

## Orchestration Philosophy
- LangGraph owns state and flow; MCP servers provide scoped tools (weather, rules, workspace, finance).
- Prefer FastMCP decorators over bespoke SDKs; expose tools/resources, then load via MCP client in nodes.
- Always route sensitive fields through a PIIMaskingNode before LLM/tool calls; favor VOEN/FIN-aware handshakes.
- Chainlit shows tool-call curtains (cot="tool_call") for trust; Langfuse records spans/latency.

## What’s Implemented (Code)
- MCP client + config: src/yonca/mcp/client.py, src/yonca/mcp/config.py.
- Weather MCP handler: src/yonca/mcp/handlers/weather_handler.py with consent/fallback + traces.
- ZekaLab MCP handler: src/yonca/mcp/handlers/zekalab_handler.py for irrigation/fertilization/pest/subsidy/harvest.
- ZekaLab MCP server: src/yonca/mcp_server/main.py (+ Dockerfile, requirements.txt).
- Tests: unit (client, handlers, server) and integration (context loader weather MCP).

## What’s Implemented (Docs)
- Phase 2/3 summaries and deployment: PHASE-2-COMPLETION-SUMMARY.md, PHASE-3-COMPLETION-SUMMARY.md, PHASE-3-DEPLOYMENT-GUIDE.md.
- Handoff: PHASE-4-HANDOFF.md, QUICK-REFERENCE.md.

## Immediate Next Work (Phase 4-5 Focus)
1) LangGraph orchestration
   - Parallel MCP calls + graceful degradation in agent nodes (context_loader, agronomist).
   - Ensure MCPTrace emitted for every tool/resource call and persisted via PostgresSaver.
2) UI + Consent
   - Chainlit MCP status badge; explicit consent prompt before external MCP calls.
3) Observability
   - Langfuse spans for MCP calls (server, tool, latency, success/error); include call_id in AgentState.
4) Safety
   - PIIMaskingNode before LLM/tool calls; VOEN/FIN handling per Sovereign AI guidance.
5) Config & Ops
   - Finalize .env template for MCP endpoints/secrets/timeouts; ensure pre-start checks cover MCP vars.

## Sovereign Developer Prompt (drop into Copilot/Cursor)
You are the Lead AI Architect for ZekaLab building ALEM (sovereign agrotech agent). Use LangGraph for all stateful flows; call external systems only via MCP (FastMCP servers). UI is Chainlit with cot="tool_call" enabled to show reasoning. Persist sessions with PostgresSaver. Always add a PIIMaskingNode before any external LLM/tool call and prefer VOEN/FIN-aware handshakes. Do not build bespoke API wrappers—expose FastMCP tools/resources and load them via the MCP client. Branding: "ALEM" or "Yonca AI" only.

## Quick Command Reminders
- Start ZekaLab MCP server: .venv\\Scripts\\python.exe -m uvicorn yonca.mcp_server.main:app --port 7777
- Run MCP tests: .venv\\Scripts\\python.exe -m pytest tests/unit/test_mcp_server/ -v
- Lint/QA: tasks → 🛡️ Pre-Start Quality Checks (includes ruff/tests/config)
