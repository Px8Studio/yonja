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
| 4 | **🔐 TLS/HTTPS (Traefik)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 2 days | **Production blocker** |
| 5 | **🔐 Secrets Management (SOPS/Vault)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 3 days | **Production blocker** |
| 6 | **🔐 Container Scanning (Trivy)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 1 day | **CI/CD gate** |
| 7 | **🔐 Network Segmentation** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 1 day | **Data isolation** |

---

## 🟠 Priority 2: Production Readiness

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 8 | **Prometheus Metrics** | ⬜ | [07-OBSERVABILITY](07-OBSERVABILITY.md) | 1 day | `alem_requests_total`, etc. |
| 9 | **🔐 RBAC (Casbin)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 3 days | Admin vs farmer roles |
| 10 | **🔐 Database Encryption (TDE)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 2 days | PostgreSQL encryption |
| 11 | **🔐 Redis AUTH** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 1 day | Redis ACL + password |
| 12 | **🔐 Security Monitoring** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 3 days | Prometheus + Grafana + Loki |
| 13 | **Chat Profiles (Personas)** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 2 days | Farmer persona selector |
| 14 | **NDVI Visualization** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 3 days | Satellite imagery display |
| 15 | **Export Chat History** | ⬜ | [11-CHAINLIT-UI](11-CHAINLIT-UI.md) | 1 day | Download conversation |

---

## 🟡 Priority 3: Quality of Life

| # | Feature | Status | Doc Reference | Effort | Notes |
|:-:|:--------|:------:|:--------------|:-------|:------|
| 16 | **Langfuse Insights Caching** | ⬜ | [03-ARCHITECTURE](03-ARCHITECTURE.md) | 1 day | Cache aggregates in App DB |
| 17 | **Version Fingerprint in Traces** | ⬜ | [12-DEPLOYMENT](12-DEPLOYMENT-PRICING.md) | 0.5 day | Log ALEM version per trace |
| 18 | **Automated Model Change Detection** | ⬜ | [12-DEPLOYMENT](12-DEPLOYMENT-PRICING.md) | 1 day | CI script for version bumps |
| 19 | **🔐 WAF (ModSecurity)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 2 days | Traefik WAF plugin |
| 20 | **🔐 Audit Logging** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 2 days | Structured JSON logs |

---

## 🟢 Priority 4: Nice to Have

| 21 | **ClickHouse for High-Volume Traces** | ⬜ | docker-compose.local.yml | 2 days | Optional Langfuse upgrade |
| 22 | **Grafana Dashboards** | ⬜ | [07-OBSERVABILITY](07-OBSERVABILITY.md) | 2 days | If Prometheus added |
| 23 | **🔐 API Gateway (Kong OSS)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 3 days | Enhanced API management |
| 24 | **🔐 SIEM (Wazuh)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 5 days | Security monitoring |
| 25 | **🔐 Runtime Protection (Falco)** | ⬜ | [17-SECURITY](17-SECURITY-ENHANCEMENT-PLAN.md) | 2 days | Container threat detection |
| 26 | **ClickHouse for High-Volume Traces** | ⬜ | docker-compose.local.yml | 2 days | Optional Langfuse upgrade |
| 13 | **Grafana Dashboards** | ⬜ | [07-OBSERVABILITY](07-OBSERVABILITY.md) | 2 days | If Prometheus added |
| 14 | **mygov ID OAuth** | 🚫 | [14-DISCOVERY](14-DISCOVERY-QUESTIONS.md) | ? | Blocked: awaiting Digital Umbrella |

---

## 🛠️ Implementation Scripts Needed

| Script | Purpose | Priority |
|:-------|:--------|:---------|
| `scripts/check_alem_version.py` | Compare model strings, auto-bump version | P1 |
| `scripts/generate_golden_dataset.py` | Template for evaluation cases | P1 |
| `scripts/export_langfuse_insights.py` | Cache Langfuse metrics to App DB | P3 |
| **🔐 Security Scripts** | | |
| `scripts/rotate_secrets.sh` | Rotate API keys and credentials | P1 |
| `scripts/scan_images.sh` | Local Trivy container scanning | P1 |
| `scripts/init_encryption.sh` | PostgreSQL TDE setup | P2 |
| `scripts/security_audit.sh` | Run all security checks | P2 |

---

## 📅 Suggested Sprint Plan

### Sprint 1 (Week 1-2) — Security Foundation
- [ ] #4 **TLS/HTTPS (Traefik)** 🔴
- [ ] #5 **Secrets Management (SOPS)** 🔴
- [ ] #6 **Container Scanning (Trivy)** 🔴
- [ ] #7 **Network Segmentation** 🔴
- [ ] #3 **ALEM Version Tracking**

### Sprint 2 (Week 3-4) — Security Hardening + Testing
- [ ] #9 **RBAC (Casbin)** 🟠
- [ ] #10 **Database Encryption** 🟠
- [ ] #11 **Redis AUTH** 🟠
- [ ] #1 **Evaluation Test Suite scaffold**

### Sprint 3 (Week 5-6) — Observability
- [ ] #8 **Prometheus Metrics** 🟠
- [ ] #12 **Security Monitoring (Grafana + Loki)** 🟠
- [ ] #13 **Chat Profiles (Personas)** 🟠
- [ ] #2 **Golden Dataset (partial)**

### Sprint 4 (Week 7-8) — Production Polish
- [ ] #14 **NDVI Visualization** 🟠
- [ ] #15 **Export Chat History** 🟠
- [ ] #19 **WAF (ModSecurity)** 🟡
- [ ] #20 **Audit Logging** 🟡
- [ ] #2 **Golden Dataset (complete)**

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
