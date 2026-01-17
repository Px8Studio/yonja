# 🧹 Yonca AI - Codebase Cleanup Guide

> **Status:** ✅ CLEANUP COMPLETE  
> The codebase is now consolidated around the **Sidecar Intelligence Architecture**.

---

## 📋 Summary

The codebase has been streamlined:
- ✅ **Removed:** Old `core/` folder (rules.py, engine.py)
- ✅ **Consolidated:** All logic lives in `sidecar/`
- ✅ **Unified:** Single `rules_registry.py` (source of truth for agronomy rules)
- ✅ **Unified:** Single `intent_matcher.py` (source of truth for Azerbaijani NLU)

---

## ✅ Current Architecture (Clean)

```
src/yonca/
├── sidecar/              # 🎯 CORE: All intelligence logic here
│   ├── rules_registry.py     # 20+ agronomy rules (AZ- prefixes)
│   ├── intent_matcher.py     # Azerbaijani intent detection
│   ├── schedule_service.py   # Daily task generation
│   ├── recommendation_service.py  # Main orchestrator
│   ├── lite_inference.py     # standard/lite/offline modes
│   ├── pii_gateway.py        # Data sanitization
│   ├── rag_engine.py         # Rule validation + LLM
│   ├── trust.py              # Confidence scoring
│   ├── digital_twin.py       # Simulation (optional)
│   ├── dialect.py            # Regional Azerbaijani
│   ├── temporal.py           # Farm timeline
│   └── validation.py         # Expert validation hooks
├── api/                  # REST + GraphQL (thin layer)
├── agent/                # LangGraph tools (optional advanced)
├── data/                 # Synthetic scenarios + generators
├── models/               # Pydantic models
└── umbrella/             # Streamlit demo UI
```

---

## 🗑️ What Was Removed

| File | Why Removed |
|------|-------------|
| `src/yonca/core/rules.py` | Merged into `sidecar/rules_registry.py` |
| `src/yonca/core/engine.py` | Merged into `sidecar/schedule_service.py` |
| `src/yonca/core/__init__.py` | Folder deprecated |
4. ⏳ Delete `core/` folder after downstream consumers migrate

### Phase 4: Model Unification
1. Consolidate all dataclasses to `models/__init__.py`
2. Remove duplicate dataclass definitions in other modules

### Phase 5: Migrate Core Consumers ✅ COMPLETED
All files importing from `yonca.core` have been migrated:

| File | Old Import | New Import | Status |
|------|------------|------------|--------|
| `api/routes.py` | `core.engine.recommendation_engine` | `sidecar.generate_daily_schedule` | ✅ Done |
| `api/graphql.py` | `core.engine.recommendation_engine` | `sidecar.generate_daily_schedule` | ✅ Done |
| `agent/tools.py` | `core.engine.recommendation_engine` | `sidecar.generate_daily_schedule` | ✅ Done |
| `tests/test_yonca.py` | `core.engine.RecommendationEngine` | `sidecar.ScheduleService` | ✅ Done |

**Deleted:** `src/yonca/core/` folder removed ✅

---

## 📊 Duplication Matrix

| Concept | Canonical Location | Duplicate Locations |
|---------|-------------------|---------------------|
| Agronomy Rules | `sidecar/rules_registry.py` | `core/rules.py` ❌, `umbrella/agronomy_rules.py` ⚠️ |
| Farm Scenarios | `data/scenarios.py` | `umbrella/scenario_manager.py` ⚠️ |
| Recommendations | `sidecar/recommendation_service.py` | `umbrella/mock_backend.py` ⚠️, ~~`core/engine.py`~~ ✅ migrated |
| Daily Schedules | `sidecar/schedule_service.py` | ~~`core/engine.py`~~ ✅ migrated |
| Intent Matching | `sidecar/intent_matcher.py` | ✅ (Already consolidated) |
| Data Models | `models/__init__.py` | Various local dataclasses ⚠️ |

---

## 🎯 Target Architecture

After cleanup, the codebase should have:

```
src/yonca/
├── sidecar/          # 🎯 CORE: Headless Intelligence Engine
│   ├── recommendation_service.py  # AI recommendations
│   ├── schedule_service.py        # Daily schedules & alerts ✅ NEW
│   ├── rules_registry.py          # Unified agronomy rules
│   └── ...
├── api/              # REST & GraphQL (consuming sidecar) ✅ MIGRATED
├── agent/            # LangGraph orchestration (consuming sidecar) ✅ MIGRATED
├── data/             # Synthetic data only
├── models/           # Unified Pydantic models
├── umbrella/         # UI only (consuming sidecar APIs)
│   ├── app.py        # Streamlit entry
│   └── styles.py     # CSS only
├── main.py           # FastAPI entry
├── config.py         # Configuration
└── startup.py        # Startup manager
```

**Deleted:**
- ✅ `core/` folder (deprecated, merged into sidecar)
- ⏳ `umbrella/mock_backend.py` (pending)
- ⏳ `umbrella/scenario_manager.py` (pending)
- ⏳ `umbrella/agronomy_rules.py` (pending)

---

*ZekaLab - Headless Intelligence as a Service*
