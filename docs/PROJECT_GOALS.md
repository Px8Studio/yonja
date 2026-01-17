# 🎯 Yonca AI - Project Goals & Success Criteria

> **The North Star:** Deliver a working AI farm assistant prototype that Digital Umbrella can integrate into their Yonca platform.

---

## 🏆 Ultimate Goal

**A farmer in Azerbaijan opens the app, types "Bu gün nə etməliyəm?" (What should I do today?), and gets a prioritized task list with rule-validated recommendations.**

---

## ✅ Success Criteria (Challenge Requirements)

| Requirement | Target | Status | How We Achieve It |
|-------------|--------|--------|-------------------|
| **Farm Scenarios** | ≥5 synthetic profiles | ✅ 7 scenarios | `data/scenarios.py` (wheat, livestock, orchard, vegetable, mixed, intensive, hazelnut) |
| **Logical Accuracy** | ≥90% | ✅ By design | `rules_registry.py` validates every LLM output against 20+ agronomy rules |
| **Data Safety** | 100% | ✅ By design | `pii_gateway.py` strips all identifiers; only synthetic data used |
| **Azerbaijani Support** | Native | ✅ Working | `intent_matcher.py` + Qwen2.5 handles Turkic language |
| **Daily Schedule** | Auto-generated | ✅ Working | `schedule_service.py` generates task lists |
| **UX Compatibility** | Yonca style | ✅ Working | `umbrella/app.py` with mobile-first CSS |
| **API Structure** | REST + GraphQL | ✅ Working | FastAPI with OpenAPI docs at `/docs` |
| **Offline Support** | Low connectivity | ✅ Working | `offline` inference mode (rules-only, <50ms) |

---

## 🎯 Core Value Proposition

**What we deliver:**
```
Farmer's Question (AZ) → Intent Detection → Rules Lookup → LLM Response → Validated Task
```

**What farmers get:**
- "Suvarma lazımdır" (Irrigation needed) → Because soil moisture <20%
- "Gübrələmə vaxtıdır" (Time to fertilize) → Because nitrogen level low
- "Peyvənd vaxtı yaxınlaşır" (Vaccination time approaching) → Because 180 days passed

**Every recommendation includes:**
- Rule citation (e.g., `AZ-IRR-001`)
- Confidence score (e.g., 0.92)
- Source (e.g., "Rulebook: Early Drought Prevention")

---

## 🏗️ Architecture Principle

**Sidecar = We never touch the core system**

```
┌─────────────────────────────────────────────────────┐
│ YONCA PLATFORM (Digital Umbrella)                   │
│ • EKTIS integration (government subsidies)          │
│ • Farmer database (real PII)                        │
│ • Financial transactions                            │
│ • ← We DON'T touch any of this                      │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ 🌿 YONCA AI SIDECAR (This Repo)                     │
│ • Synthetic farm scenarios only                     │
│ • Rule-validated recommendations                    │
│ • PII-stripped processing                           │
│ • Ready-to-plug API contract                        │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Key Files (Where Things Live)

| What | File | Purpose |
|------|------|---------|
| **Agronomy Rules** | `sidecar/rules_registry.py` | Single source of truth (AZ- prefixes) |
| **Intent Detection** | `sidecar/intent_matcher.py` | Azerbaijani NLU patterns |
| **Task Generation** | `sidecar/schedule_service.py` | Daily schedule logic |
| **Main Orchestrator** | `sidecar/recommendation_service.py` | Full pipeline coordinator |
| **Data Sanitization** | `sidecar/pii_gateway.py` | Zero-trust PII handling |
| **LLM Inference** | `sidecar/lite_inference.py` | Standard/lite/offline modes |
| **Farm Scenarios** | `data/scenarios.py` | 7 synthetic farm profiles |
| **Demo UI** | `umbrella/app.py` | Streamlit prototype |

---

## 🚀 How to Demo

1. **Start the server:**
   ```bash
   python -m yonca.startup
   ```

2. **Open API docs:**
   http://localhost:8000/docs

3. **Test a recommendation:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/recommendations \
     -H "Content-Type: application/json" \
     -d '{"farm_id": "scenario-wheat"}'
   ```

4. **Run Streamlit demo:**
   ```bash
   streamlit run src/yonca/umbrella/app.py
   ```

---

## 📊 What "Done" Looks Like

- [x] 7 synthetic farm scenarios
- [x] 20+ agronomy rules with AZ- prefixes
- [x] Intent matcher for Azerbaijani
- [x] Daily schedule generator
- [x] REST API with OpenAPI docs
- [x] PII gateway for data safety
- [x] 3 inference modes (standard/lite/offline)
- [x] Streamlit demo UI
- [x] Consolidated codebase (no duplicate logic)

**Ready for integration** = Digital Umbrella can point their app at our API and get recommendations.

---

## 🔮 Future (Phase 2)

Once integrated with real Yonca platform:
1. Replace synthetic scenarios with real farm data hooks
2. Connect to real weather API (not simulated)
3. Add EKTIS subsidy deadline alerts
4. Expand to more crop types and regions

**The sidecar design means ZERO code changes for Phase 2—just flip the data source.**
