# 📚 LangGraph Documentation - Core Reference

> **Updated:** January 22, 2026
> **Status:** Consolidated for clarity (removed 4 redundant docs)

---

## 🎯 START HERE: Master Guide

### [LANGGRAPH_ARCHITECTURE_GUIDE.md](./LANGGRAPH_ARCHITECTURE_GUIDE.md) ⭐

**Everything you need to know about LangGraph's role:**
- Dev vs Production distinction (crystal-clear)
- Component relationship matrix (who talks to whom)
- Multi-channel architecture (Chainlit + Mobile + Bot)
- Recommended ZekaLab production stack
- Pro-tip: `langgraph build` for production
- Current UI implementation (model selection + interaction mode)

**Read time:** 15 min | **Covers:** 90% of common questions

---

## 🧪 Testing & Integration

### [LANGGRAPH_TESTING_GUIDE.md](./LANGGRAPH_TESTING_GUIDE.md)

**How to test LangGraph execution:**
- Unit test patterns for graph client
- Integration tests for FastAPI routes
- End-to-end scenarios
- Mock fixtures

**Read time:** 10 min | **When needed:** Writing tests

---

## 🐳 Deployment

### [LANGGRAPH_DOCKER_DEPLOYMENT.md](./LANGGRAPH_DOCKER_DEPLOYMENT.md)

**Docker-specific configuration:**
- Docker Compose setup for development
- Standalone Docker container instructions
- Service profiles and networking
- Health checks and logging

**Read time:** 8 min | **When needed:** Setting up Docker

---

## 📊 Archived / Consolidated Documents

> These documents have been **consolidated into LANGGRAPH_ARCHITECTURE_GUIDE.md**. Keep for reference but prefer the master guide.

| Old Document | Consolidated Into | Reason |
|--------------|-------------------|--------|
| LANGGRAPH_EXECUTIVE_SUMMARY.md | LANGGRAPH_ARCHITECTURE_GUIDE.md | Summary now in master guide |
| LANGGRAPH_ARCHITECTURE_COMPARISON.md | LANGGRAPH_ARCHITECTURE_GUIDE.md | Diagrams integrated |
| LANGGRAPH_DEV_SERVER_FULL_ROLE_ANALYSIS.md | LANGGRAPH_ARCHITECTURE_GUIDE.md | Concepts merged |
| LANGGRAPH_DEV_SERVER_IMPLEMENTATION_GUIDE.md | LANGGRAPH_ARCHITECTURE_GUIDE.md | Implementation moved to Docker doc |
| LANGGRAPH_DEV_SERVER_STARTUP.md | LANGGRAPH_DOCKER_DEPLOYMENT.md | Startup instructions merged |
