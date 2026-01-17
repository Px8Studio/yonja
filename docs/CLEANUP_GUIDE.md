# 🧹 Yonca AI - Codebase Cleanup Guide

> **ZekaLab** - Headless Intelligence as a Service
> 
> This document identifies stale, duplicate, and consolidation-ready files in the codebase.

---

## 📋 Summary

The codebase has evolved with two parallel implementations:
1. **Original "core" implementation** - older, partially deprecated
2. **Sidecar architecture** - canonical, headless API design

This guide helps you safely remove redundant code and consolidate to the Sidecar model.

---

## 🗑️ FILES TO DELETE

### Immediate Deletion (Safe)

| File | Status | Reason |
|------|--------|--------|
| `src/yonca/core/rules.py` | ✅ **DELETED** | Consolidated into `sidecar/rules_registry.py`. |
| `src/yonca/core/engine.py` | ✅ **DELETED** | Migrated to `sidecar/schedule_service.py`. |
| `src/yonca/core/__init__.py` | ✅ **DELETED** | Entire `core/` folder removed. |

### Delete After Migration

| File | Status | Migration Target | Notes |
|------|--------|------------------|-------|
| `src/yonca/umbrella/mock_backend.py` | 🟡 **DUPLICATE** | `sidecar/recommendation_service.py` | Has 781 lines of mock backend that duplicates sidecar logic. Refactor `umbrella/app.py` to consume sidecar APIs instead. |
| `src/yonca/umbrella/scenario_manager.py` | 🟡 **DUPLICATE** | `data/scenarios.py` | Duplicates farm scenario data with different dataclass. |
| `src/yonca/umbrella/agronomy_rules.py` | 🟡 **DUPLICATE** | `sidecar/rules_registry.py` | Separate rules definitions with different rule IDs. |

---

## ⚠️ FILES NEEDING REVIEW

### Uncertain Status

| File | Issue | Action Required |
|------|-------|-----------------|
| `src/yonca/api/graphql.py` | May be unused | Verify if GraphQL is actively consumed by any frontend |
| `src/yonca/agent/tools.py` | LangGraph integration | Verify integration plan with sidecar architecture |

---

## ✅ FILES TO KEEP (Canonical)

### Sidecar Intelligence Engine (Core)
- ✅ `src/yonca/sidecar/pii_gateway.py` - Zero-trust data sanitization
- ✅ `src/yonca/sidecar/rag_engine.py` - RAG with agronomy rulebook
- ✅ `src/yonca/sidecar/rules_registry.py` - Unified agronomy rules (AZ- prefixes)
- ✅ `src/yonca/sidecar/intent_matcher.py` - Consolidated intent detection
- ✅ `src/yonca/sidecar/lite_inference.py` - Edge-optimized inference
- ✅ `src/yonca/sidecar/trust.py` - Confidence scoring
- ✅ `src/yonca/sidecar/digital_twin.py` - Simulation engine
- ✅ `src/yonca/sidecar/dialect.py` - Regional Azerbaijani normalization
- ✅ `src/yonca/sidecar/temporal.py` - Farm timeline memory
- ✅ `src/yonca/sidecar/validation.py` - Input validation
- ✅ `src/yonca/sidecar/data_adapter.py` - Data transformation
- ✅ `src/yonca/sidecar/recommendation_service.py` - Recommendation generation
- ✅ `src/yonca/sidecar/schedule_service.py` - **NEW** Daily schedule & alerts (migrated from core/engine.py)
- ✅ `src/yonca/sidecar/api_routes.py` - Sidecar REST API

### Data Layer
- ✅ `src/yonca/data/scenarios.py` - Canonical farm scenarios
- ✅ `src/yonca/data/generators.py` - Synthetic data generators
- ✅ `src/yonca/models/__init__.py` - Canonical Pydantic models

### API Layer
- ✅ `src/yonca/api/routes.py` - REST API endpoints
- ✅ `src/yonca/main.py` - FastAPI entry point

### UI Layer (Keep but Refactor)
- ✅ `src/yonca/umbrella/app.py` - Streamlit UI (refactor to consume sidecar)
- ✅ `src/yonca/umbrella/styles.py` - Pure CSS styling (no duplication)

---

## 🔄 CONSOLIDATION ROADMAP

### Phase 1: Immediate Cleanup
```bash
# Safe to delete now
rm src/yonca/core/rules.py
```

### Phase 3: Evaluate Core Module ✅ COMPLETED
1. ✅ Audited `core/engine.py` for unique logic not in sidecar
2. ✅ Migrated valuable logic to `sidecar/schedule_service.py`:
   - `ScheduleService` class (daily schedule generation)
   - `generate_daily_schedule()` convenience function
   - `_generate_alerts()` (weather-based alert generation)
   - `TASK_DURATION_ESTIMATES` (task duration mapping)
3. ✅ Added deprecation warnings to `core/` folder
   - `core/__init__.py` emits DeprecationWarning on import
   - `RecommendationEngine` emits DeprecationWarning on instantiation
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
