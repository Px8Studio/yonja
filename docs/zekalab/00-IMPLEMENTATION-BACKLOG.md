# 📋 ALEM Implementation Backlog

> **Purpose:** Track unimplemented but aspired features extracted from documentation review.

---

## 📊 Status Legend

| Status | Icon | Meaning |
|:-------|:----:|:--------|
| Not Started | ⬜ | Documented but not implemented |
| In Progress | 🔄 | Currently being worked on |
| Blocked | 🚫 | Waiting on external dependency |
| Done | ✅ | Implemented and tested |

---

## 🔴 Priority 1: Critical Path

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 1 | **Evaluation Test Suite** | ⬜ | [04-TESTING](04-TESTING-STRATEGY.md) | 5 days | `tests/evaluation/` is empty |
| 2 | **Golden Dataset (105+ cases)** | ⬜ | [04-TESTING](04-TESTING-STRATEGY.md) | 10 days | Requires agronomist input |
| 3 | **ALEM Version Tracking** | ⬜ | [12-DEPLOYMENT](12-DEPLOYMENT-PRICING.md) | 1 day | `alem_version.toml` + CI check |

---

## 🟠 Priority 2: Production Readiness

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 4 | **Prometheus Metrics** | ⬜ | [07-OBSERVABILITY](07-OBSERVABILITY.md) | 1 day | `alem_requests_total`, etc. |
| 5 | **RBAC (Role-Based Access)** | ⬜ | [08-SECURITY](08-SECURITY.md) | 3 days | Admin vs farmer roles |
| 6 | **Chat Profiles (Personas)** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 2 days | Farmer persona selector |
| 7 | **NDVI Visualization** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 3 days | Satellite imagery display |
| 8 | **Export Chat History** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 1 day | Download conversation |

---

## 🟡 Priority 3: Quality of Life

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 9 | **Langfuse Insights Caching** | ⬜ | [03-ARCHITECTURE](03-ARCHITECTURE.md) | 1 day | Cache aggregates in App DB |
| 10 | **Version Fingerprint in Traces** | ⬜ | [12-DEPLOYMENT](12-DEPLOYMENT-PRICING.md) | 0.5 day | Log ALEM version per trace |
| 11 | **Automated Model Change Detection** | ⬜ | [12-DEPLOYMENT](12-DEPLOYMENT-PRICING.md) | 1 day | CI script for version bumps |

---

## 🟢 Priority 4: Nice to Have

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 12 | **ClickHouse for High-Volume Traces** | ⬜ | docker-compose.local.yml | 2 days | Optional Langfuse upgrade |
| 13 | **Grafana Dashboards** | ⬜ | [07-OBSERVABILITY](07-OBSERVABILITY.md) | 2 days | If Prometheus added |
| 14 | **mygov ID OAuth** | 🚫 | [14-DISCOVERY](14-DISCOVERY-QUESTIONS.md) | ? | Blocked: awaiting Digital Umbrella |

---

## 🛠️ Implementation Scripts Needed

| Script | Purpose | Priority |
|:-------|:--------|:---------|
| `scripts/check_alem_version.py` | Compare model strings, auto-bump version | P1 |
| `scripts/generate_golden_dataset.py` | Template for evaluation cases | P1 |
| `scripts/export_langfuse_insights.py` | Cache Langfuse metrics to App DB | P3 |

---

## 📅 Suggested Sprint Plan

### Sprint 1 (Week 1-2)
- [ ] #3 ALEM Version Tracking
- [ ] #1 Evaluation Test Suite scaffold
- [ ] #10 Version Fingerprint in Traces

### Sprint 2 (Week 3-4)
- [ ] #4 Prometheus Metrics
- [ ] #6 Chat Profiles (Personas)
- [ ] #2 Golden Dataset (partial)

### Sprint 3 (Week 5-6)
- [ ] #5 RBAC
- [ ] #7 NDVI Visualization
- [ ] #2 Golden Dataset (complete)

---

## 📝 How to Update This Document

1. Move items to ✅ when implemented
2. Add new items discovered during development
3. Update effort estimates based on experience
4. Link PRs/commits in Notes column

---

<div align="center">

**Last Updated:** January 20, 2026  
**Owner:** Zekalab Team

</div>
