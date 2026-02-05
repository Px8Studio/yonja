# 📋 ALİM Implementation Backlog

> **Updated:** January 2026

---

## ✅ Recent Completions

### MCP Integration (Complete ✅)
- ✅ ZekaLab FastMCP Server with 5 tools (irrigation, fertilization, pest control, subsidy, harvest)
- ✅ `langchain-mcp-adapters` integration for official MCP protocol compliance
- ✅ LangGraph ToolNode auto-binding for MCP tools
- ✅ Chainlit file upload support
- ✅ MCP health checks in welcome message

### Chat Profiles (Complete ✅)
- ✅ Expertise-based AI behavior via system prompts
- ✅ Farm scenario planning with agrotechnological calendar

---

## 🏛️ Legal & Intellectual Property

> **New Category:** IP protection and legal requirements for ALİM brand. See [19-IP-PROTECTION](19-IP-PROTECTION.md) for full details.

| # | Item | Status | Effort | Priority | Notes |
|:-:|:-----|:------:|:-------|:--------:|:------|
| L.1 | **ALİM Trademark Registration** | ⬜ | 3-5 mo | 🔴 | Class 9/42/35 with IP Agency |
| L.2 | **Software Copyright Filing** | ⬜ | 2-4 wk | 🔴 | Register LangGraph/Chainlit code |
| L.3 | **Database Rights Filing** | ⬜ | 2-4 wk | 🟠 | Training data protection |
| L.4 | **Trade Secret NDA Template** | ⬜ | 1 wk | 🟠 | For model weights |
| L.5 | **DigiRella IP Clause Draft** | ⬜ | 1 wk | 🔴 | Proposal addendum |
| L.6 | **Internal License Agreement** | ⬜ | 1 wk | 🔴 | Exclusive license with reversion right |
| L.7 | **KOBİA Startup Cert. App** | ⬜ | 2-4 wk | 🔴 | For 3-year tax exemption |
| L.8 | **IP Ownership Clause Draft** | ⬜ | 3 days | 🔴 | For internal partner agreement |

---

## 🎯 Strategic Priorities & Certifications

> High-level partnerships and legal/regulatory requirements for enterprise deployment.

| # | Item | Status | Effort | Blocking | Notes |
|:-:|:-----|:------:|:-------|:---------|:------|
| S.1 | **TPP Accreditation (CBAR)** | ⬜ | 4-6 weeks | External review | Apply for AISP role via [fintech.cbar.az](https://fintech.cbar.az) |
| S.2 | **QWAC Certificate (SİMA)** | ⬜ | 1-2 weeks | S.1 | Obtain from SİMA Partner Portal (~$500-2k/year) |
| S.3 | **DigiRella Partnership Agreement** | ⬜ | 2-4 weeks | Business negotiation | Formal API access + revenue share terms |
| S.4 | **Ministry of Agriculture Data Sharing Protocol** | ⬜ | 4-8 weeks | Government approval | G2B protocol for EKTİS direct access (Option B) |
| S.5 | **AzInTelecom GPU Cloud Contract** | ⬜ | 2-3 weeks | Procurement | Production hosting for Phase 2 |

---

## 🌐 Enterprise Integration (Phase 1-5)

> **Strategic partnerships** for scaling ALEM. See [18-ENTERPRISE-INTEGRATION-ROADMAP](18-ENTERPRISE-INTEGRATION-ROADMAP.md) for full details.

### Phase 1: Authentication (Q1-Q2 2026)

| # | Partner | Status | Effort | Priority | Notes |
|:-:|:--------|:------:|:-------|:--------:|:------|
| 1.1 | **SİMA/ASAN Login** | ⬜ | 3-4 weeks | 🔴 | Replace OAuth with sovereign auth |
| 1.2 | **SİMA Test Environment Access** | ⬜ | 1 week | 🔴 | Apply via [sima.az/en](https://sima.az/en) Partner Portal |
| 1.3 | **Biometric SDK Integration** | ⬜ | 2 weeks | 🔴 | Face ID auth for mobile |

### Phase 2: Core Data Services (Q2-Q3 2026)

| # | Partner | Status | Effort | Priority | Notes |
|:-:|:--------|:------:|:-------|:--------:|:------|
| 2.1 | **EKTİS Hot-Swap (Option A)** | ⬜ | 4-6 weeks | 🔴 | Via DigiRella/ALİM Mobile API |
| 2.2 | **EKTİS Direct API (Option B)** | ⬜ | 6-8 weeks | 🟠 | Separate Ministry partnership |
| 2.3 | **CBAR Open Banking (AIS)** | ⬜ | 4-6 weeks | 🟠 | Account information service |
| 2.4 | **Weather APIs (Azerbaijan Meteorology)** | ⬜ | 1-2 weeks | 🟠 | Hyperlocal forecasts |
| 2.5 | **AzInTelecom GPU Deployment** | ⬜ | 2-3 weeks | 🔴 | Self-hosted LLM production |

### Phase 3: Premium Intelligence (Q3-Q4 2026)

| # | Partner | Status | Effort | Priority | Notes |
|:-:|:--------|:------:|:-------|:--------:|:------|
| 3.1 | **Azərkosmos Satellite Data** | ⬜ | 8-10 weeks | 🟡 | Real NDVI feeds, 1M+ hectares |
| 3.2 | **State Tax Service (VOEN)** | ⬜ | 2-3 weeks | 🟡 | Business verification API |
| 3.3 | **CBAR Open Banking (PIS)** | ⬜ | 4-6 weeks | 🟡 | Payment initiation service |

### Phase 4: Commercial Partnerships (Q4 2026 - Q1 2027)

| # | Partner | Status | Effort | Priority | Notes |
|:-:|:--------|:------:|:-------|:--------:|:------|
| 4.1 | **PASHA Bank Advisory API** | ⬜ | 3-4 weeks | 🟢 | Agro loan recommendations |
| 4.2 | **ABB Developer Portal** | ⬜ | 3-4 weeks | 🟢 | Corporate finance integration |

### Phase 5: Enterprise B2B (Q1 2027+)

| # | Partner | Status | Effort | Priority | Notes |
|:-:|:--------|:------:|:-------|:--------:|:------|
| 5.1 | **SAP BTP Integration** | ⬜ | 12+ weeks | 🟢 | OData API for agro holdings |
| 5.2 | **Oracle Cloud Integration** | ⬜ | 12+ weeks | 🟢 | REST services for corporate farms |

---

## 🔴 Critical Path (Production Blockers)

| # | Feature | Status | Effort | Notes |
|:-:|:--------|:------:|:-------|:------|
| C.1 | Evaluation Test Suite | ⬜ | 5 days | `tests/evaluation/` empty |
| C.2 | Golden Dataset (105+ cases) | ⬜ | 10 days | Requires agronomist input |
| C.3 | TLS/HTTPS (Traefik) | ⬜ | 2 days | Production blocker |
| C.4 | Secrets Management (SOPS/Vault) | ⬜ | 3 days | Production blocker |
| C.5 | Container Scanning (Trivy) | ⬜ | 1 day | CI/CD gate |

---

## 🟠 Production Readiness

### Observability
| # | Feature | Status | Effort |
|:-:|:--------|:------:|:-------|
| P.1 | Prometheus Metrics | ⬜ | 1 day |
| P.2 | Grafana Dashboards | ⬜ | 2 days |

### Security
| # | Feature | Status | Effort |
|:-:|:--------|:------:|:-------|
| P.3 | RBAC (Casbin) | ⬜ | 3 days |
| P.4 | Redis AUTH + ACL | ⬜ | 1 day |
| P.5 | Database Encryption (TDE) | ⬜ | 2 days |

### UI/UX
| # | Feature | Status | Effort |
|:-:|:--------|:------:|:-------|
| P.6 | NDVI Visualization | ⬜ | 3 days |
| P.7 | Export Chat History | ⬜ | 1 day |
| P.8 | Multi-Language (en/ru/tr) | ⬜ | 5 days |

---

## 🟡 Enterprise Integration

| Phase | Partner | Status | Priority |
|:------|:--------|:------:|:--------:|
| 1 | SİMA/ASAN Login | ⬜ | 🔴 |
| 2 | EKTİS via DigiRella | ⬜ | 🔴 |
| 2 | CBAR Open Banking | ⬜ | 🟠 |
| 3 | Azərkosmos Satellite | ⬜ | 🟡 |

> **Full details:** See [18-ENTERPRISE-INTEGRATION-ROADMAP.md](18-ENTERPRISE-INTEGRATION-ROADMAP.md)

---

## 🟢 Future R&D

| Feature | Status | Notes |
|:--------|:------:|:------|
| Postgres MCP (NL-to-SQL) | 🔮 | Natural language database queries |
| Docling MCP (documents) | 🔮 | PDF/document processing |
| ALEM as MCP Server | 🔮 | Expose agent to external systems |
| Voice Input/Output | ⬜ | Azerbaijani TTS |
| WhatsApp Bot | ⬜ | Reach farmers via WhatsApp |

---

## 📊 Status Legend

| Icon | Meaning |
|:----:|:--------|
| ✅ | Completed |
| 🔄 | In Progress |
| ⬜ | Not Started |
| 🔮 | Planned (future) |
| 🚫 | Blocked |
