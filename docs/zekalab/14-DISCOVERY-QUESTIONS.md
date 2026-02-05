# 🔍 ALİM — Discovery Questions for Digital Umbrella

> **Purpose:** Prioritized list of questions to validate assumptions and reduce integration risk before prototype handoff.

---

## 📋 Document Information

| Field | Value |
|:------|:------|
| **Version** | 1.0 |
| **Date** | January 17, 2026 |
| **Status** | Pending Review |
| **Owner** | Zekalab Team |
| **Recipient** | Digital Umbrella IT Team |

---

## 🎯 Executive Summary

Our team has developed comprehensive technical documentation for the ALİM Sidecar prototype. During this process, we identified several assumptions that require validation from your IT team to ensure:

1. **Seamless integration** with existing ALİM infrastructure
2. **Schema compatibility** for future "hot-swap" from synthetic to real data
3. **Compliance** with security, legal, and operational requirements
4. **UX alignment** with your mobile app design system

This document contains **36 questions** organized by priority and category. We request responses to at least the **🔴 Critical** items before finalizing the prototype.

---

## ⚡ Priority Legend

| Priority | Symbol | Meaning | Impact if Unanswered |
|:---------|:-------|:--------|:---------------------|
| **Critical** | 🔴 | Blocks core functionality | Prototype may not integrate |
| **High** | 🟠 | Affects major features | Significant rework risk |
| **Medium** | 🟡 | Improves quality | Suboptimal implementation |
| **Low** | 🟢 | Nice to have | Minor adjustments |

---

## ✅ Prioritized Question Checklist

### 🔴 CRITICAL — Must Answer Before Handoff

These questions, if answered incorrectly, could require **significant architectural changes**.

---

#### Authentication & Security

- [ ] **Q1.** What is the exact format and structure of the JWT token issued by mygov ID?
  - Specifically: claims included, expiration policy, signing algorithm (RS256/HS256?)
  - *Our assumption: Standard JWT with `user_id`, `exp`, `iat` claims*

- [ ] **Q2.** How should we validate JWT tokens?
  - Option A: Call a validation endpoint you provide
  - Option B: Validate locally using a public key (please provide)
  - *Our assumption: Local validation with public key*

- [ ] **Q3.** What user attributes are available in the authenticated session?
  - Do we get: `user_id`, `region_code`, `farm_ids`, `subscription_tier`?
  - *Our assumption: Only `user_id` is guaranteed; we map to synthetic profiles*

---

#### Data Schema Compatibility

- [ ] **Q4.** Can you provide the EKTIS database schema (or sanitized version) for:
  - Parcels / Land plots
  - Sowing declarations
  - NDVI / Satellite readings
  - Crop types and codes
  - *Our assumption: We've reverse-engineered schema from public information*

- [ ] **Q5.** What is the exact format of identifiers in your system?
  - Parcel IDs: *We assumed `AZ-{REGION}-{NUMBER}` format*
  - Declaration IDs: *We assumed `DECL-{YEAR}-{NUMBER}` format*
  - User IDs: *We assumed UUIDs*

- [ ] **Q6.** What crop type codes/names are used in EKTIS?
  - *We use Azerbaijani names: Buğda, Pambıq, Üzüm, etc.*
  - Are there numeric codes or English equivalents required?

---

#### Infrastructure & Deployment

- [ ] **Q7.** Are there data residency requirements?
  - Must all data processing occur within Azerbaijan?
  - *Impact: Cloud LLM mode (Gemini API) sends data to Google servers*

- [ ] **Q8.** Where should the AI Sidecar be hosted?
  - Option A: Your infrastructure (Azure/AWS/on-premise)
  - Option B: Standalone Docker we provide
  - Option C: Our cloud deployment (Render.com)
  - *Our assumption: Dockerized microservice, deployment location flexible*

- [ ] **Q9.** Are there firewall/network restrictions for outbound API calls?
  - Weather APIs, LLM APIs (Gemini), external services
  - *Impact: May require fully offline/local-only mode*

---

#### Mobile App Integration

- [ ] **Q10.** Do you currently use WebSockets or SSE for existing chat/messaging features in ALİM?
  - If yes, which protocol and what is the message format?
  - If no real-time features exist, do you support SSE or WebSocket in your mobile framework?
  - *This determines how we stream the agent's "thinking" responses*
  - *Our design uses SSE — we can adapt to match your existing patterns*

- [ ] **Q11.** What is the mobile framework used?
  - Flutter / React Native / Native Android+iOS
  - *Affects our integration approach and SDK recommendations*

---

#### AI State & Memory Ownership

- [ ] **Q12.** Where should AI conversation state (memory) be stored?
  - Option A: **Our module's database** (Redis/PostgreSQL) — we manage persistence
  - Option B: **Your system** — we return state via API, you store it
  - Option C: **Hybrid** — short-term in our Redis, long-term synced to your system
  - *Affects: data ownership, privacy compliance, session recovery, and integration complexity*
  - *Our current design: Redis for session state, PostgreSQL for synthetic profiles*

---

### 🟠 HIGH — Strongly Recommended Before Handoff

These affect major features and user experience.

---

#### API Contract

- [ ] **Q13.** What is your API versioning strategy?
  - Path-based (`/api/v1/`), header-based, query param?
  - *Our endpoint: `/ALİM-ai/chat` — should this change?*

- [ ] **Q14.** What error response format do you use?
  ```json
  // Our assumed format:
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Input too long",
      "details": {}
    }
  }
  ```
  - Please confirm or provide your standard format

- [ ] **Q15.** Do you prefer REST or GraphQL for the sidecar API?
  - *We've designed REST-first, but can adapt*

- [ ] **Q16.** Is there an API gateway in front of your services?
  - Kong, Apigee, AWS API Gateway, Azure APIM?
  - *Affects rate limiting and auth handling*

---

#### UX & Design System

- [ ] **Q17.** Can you share the Figma/Sketch design system files?
  - Or at minimum: exact hex codes, typography specs, spacing grid
  - *We reverse-engineered: Primary `#2E7D32`, Accent `#4CAF50`*

- [ ] **Q18.** What defines "UX compatibility" in scoring criteria (20%)?
  - Visual match to existing app?
  - API response format alignment?
  - Navigation placement approval?

- [ ] **Q19.** Where should the AI Assistant tab be placed in navigation?
  - *We proposed: Between "Məntəqələr" and "Təsərrüfatlarım"*
  - Is this acceptable or do you have a different preference?

---

#### Language & Content

- [ ] **Q20.** Do farmers use formal or informal Azerbaijani in the app?
  - Formal: "Siz suvarmalısınız" vs Informal: "Sən suvarmalısan"
  - *Our chatbot uses formal tone — please confirm*

- [ ] **Q21.** Do you have an existing glossary of agricultural terms in Azerbaijani?
  - For irrigation, fertilization, pest control, etc.
  - *We can align our vocabulary to match*

- [ ] **Q22.** Can you share anonymized examples of how farmers phrase questions?
  - Support tickets, FAQ queries, search logs
  - *Improves our intent detection accuracy*

---

#### Business Rules

- [ ] **Q23.** What agronomic guidelines/standards do you currently reference?
  - Ministry of Agriculture rules?
  - International standards (FAO)?
  - Internal expert knowledge base?
  - *Our "agronomy rulebook" is research-based — should align with yours*

- [ ] **Q24.** Are there topics the AI must NEVER provide advice on?
  - Specific pesticide brands?
  - Financial/loan advice?
  - Veterinary medical advice?
  - *We need explicit guardrail requirements*

---

### 🟡 MEDIUM — Improves Quality & Reduces Risk

---

#### Authentication (Extended)

- [ ] **Q25.** Is there a test/sandbox mygov ID environment for development?
  - Test credentials or mock auth server?

- [ ] **Q26.** How should the sidecar handle token refresh during long sessions?
  - Auto-refresh? Prompt re-auth? Session timeout?

---

#### Data & Schema (Extended)

- [ ] **Q27.** How frequently is NDVI/satellite data updated in EKTIS?
  - Daily, weekly, on-demand?
  - *Affects our synthetic time-series generation patterns*

- [ ] **Q28.** What sowing declaration statuses exist?
  - *We assumed: PENDING, CONFIRMED, REJECTED*
  - Are there others: EXPIRED, AMENDED, CANCELLED?

- [ ] **Q29.** What are the subsidy application deadlines by crop type?
  - *Critical for subsidy-related AI recommendations*

---

#### Operations

- [ ] **Q30.** What monitoring/logging stack do you use?
  - Prometheus + Grafana? ELK? Azure Monitor? Datadog?
  - *Our observability design should integrate*

- [ ] **Q31.** What CI/CD pipeline and container registry do you use?
  - GitHub Actions? GitLab CI? Azure DevOps?
  - *For deployment automation handoff*

- [ ] **Q32.** What correlation/request ID format do you use for tracing?
  - UUID? Specific prefix?
  - *For debugging across services*

---

### 🟢 LOW — Nice to Have

---

#### Evaluation & Demo

- [ ] **Q33.** How will "≥90% logical accuracy" be measured?
  - Will you provide a test dataset?
  - Specific evaluation rubric?
  - Manual expert review?

- [ ] **Q34.** What specific scenarios must the 5 farm profiles cover?
  - You mentioned: wheat, livestock, orchard
  - Are there mandatory profiles (e.g., cotton, vegetable)?

- [ ] **Q35.** What is the preferred demo format?
  - Live demo? Recorded video?
  - Specific duration requirements?

- [ ] **Q36.** How do you handle offline/low-connectivity today in the app?
  - Local caching strategy? Offline-first architecture?
  - *Our "lightweight model concept" should align*

---

## 📊 Questions Summary

| Category | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | Total |
|:---------|:-----------:|:-------:|:---------:|:------:|:-----:|
| Authentication | 3 | 0 | 2 | 0 | 5 |
| Data Schema | 3 | 0 | 3 | 0 | 6 |
| Infrastructure | 3 | 1 | 2 | 0 | 6 |
| Mobile/UX | 2 | 3 | 0 | 1 | 6 |
| AI State/Memory | 1 | 0 | 0 | 0 | 1 |
| API Contract | 0 | 4 | 0 | 0 | 4 |
| Language | 0 | 3 | 0 | 0 | 3 |
| Business Rules | 0 | 2 | 1 | 0 | 3 |
| Evaluation | 0 | 0 | 0 | 3 | 3 |
| **TOTAL** | **12** | **13** | **8** | **4** | **37** |

---

## 🚨 Critical Assumptions at Risk

If we don't receive answers to these questions, the following **high-risk assumptions** will proceed as-is:

| Assumption | Risk Level | Fallback Plan |
|:-----------|:-----------|:--------------|
| JWT tokens can be validated locally with a public key | 🔴 Critical | Implement mock auth for demo |
| EKTIS schema matches our reverse-engineered model | 🔴 Critical | Schema migration script on handoff |
| Mobile app supports SSE streaming | 🔴 Critical | Fallback to polling-based responses |
| No data residency restrictions | 🔴 Critical | Default to local-only (Ollama) mode |
| AI state stored in our Redis/PostgreSQL | 🔴 Critical | Add state export API endpoint |
| Crop types use Azerbaijani names directly | 🟠 High | Mapping table in configuration |
| Primary color is `#2E7D32` | 🟡 Medium | CSS variables for easy change |
| Formal Azerbaijani tone is appropriate | 🟡 Medium | Configurable prompt templates |

---

## 📅 Requested Response Timeline

| Priority | Requested By | Reason |
|:---------|:-------------|:-------|
| 🔴 Critical | **ASAP / Within 3 days** | Blocks architecture decisions |
| 🟠 High | Within 1 week | Affects feature implementation |
| 🟡 Medium | Within 2 weeks | Quality improvements |
| 🟢 Low | Before demo | Polish and evaluation prep |

---

## 📬 Response Format

Please respond in any format convenient for you:
- Email with numbered answers
- Shared document with comments
- Video call for complex topics
- Access to relevant documentation/systems

For technical details (schemas, tokens), **examples or documentation links** are preferred over verbal descriptions.

---

## 📞 Contact

For questions about this document or to schedule a technical discussion:

| Contact | Details |
|:--------|:--------|
| **Email** | [Your team email] |
| **Phone** | [Your contact number] |
| **Preferred Meeting Times** | [Your availability] |

---

<div align="center">

**📄 Document:** `14-DISCOVERY-QUESTIONS.md`
**🔗 Part of:** ALİM Sidecar Technical Documentation
**📚 See also:** [01-MANIFESTO.md](01-MANIFESTO.md) | [03-ARCHITECTURE.md](03-ARCHITECTURE.md)

</div>
