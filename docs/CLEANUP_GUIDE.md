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
| `src/yonca/core/rules.py` | 🔴 **DEPRECATED** | Contains explicit deprecation notice. Already consolidated into `sidecar/rules_registry.py`. |

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
| `src/yonca/core/engine.py` | Parallel implementation | Evaluate if sidecar fully replaces this; may have unique logic worth preserving |
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

### Phase 2: Refactor Umbrella App
1. Update `umbrella/app.py` to import from `sidecar/` instead of `mock_backend.py`
2. Replace `MockYoncaBackend` with sidecar services
3. Delete `umbrella/mock_backend.py`
4. Delete `umbrella/scenario_manager.py` (use `data/scenarios.py`)
5. Delete `umbrella/agronomy_rules.py` (use `sidecar/rules_registry.py`)

### Phase 3: Evaluate Core Module
1. Audit `core/engine.py` for unique logic not in sidecar
2. Migrate any valuable logic to sidecar modules
3. Consider deprecating entire `core/` folder

### Phase 4: Model Unification
1. Consolidate all dataclasses to `models/__init__.py`
2. Remove duplicate dataclass definitions in other modules

---

## 📊 Duplication Matrix

| Concept | Canonical Location | Duplicate Locations |
|---------|-------------------|---------------------|
| Agronomy Rules | `sidecar/rules_registry.py` | `core/rules.py` ❌, `umbrella/agronomy_rules.py` ⚠️ |
| Farm Scenarios | `data/scenarios.py` | `umbrella/scenario_manager.py` ⚠️ |
| Recommendations | `sidecar/recommendation_service.py` | `umbrella/mock_backend.py` ⚠️, `core/engine.py` ⚠️ |
| Intent Matching | `sidecar/intent_matcher.py` | ✅ (Already consolidated) |
| Data Models | `models/__init__.py` | Various local dataclasses ⚠️ |

---

## 🎯 Target Architecture

After cleanup, the codebase should have:

```
src/yonca/
├── sidecar/          # 🎯 CORE: Headless Intelligence Engine
├── api/              # REST & GraphQL (consuming sidecar)
├── agent/            # LangGraph orchestration (consuming sidecar)
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
- ❌ `core/` folder (deprecated, merged into sidecar)
- ❌ `umbrella/mock_backend.py`
- ❌ `umbrella/scenario_manager.py`
- ❌ `umbrella/agronomy_rules.py`

---

*ZekaLab - Headless Intelligence as a Service*
