# 🛡️ Quality Gate System — Quick Setup

## TL;DR

Automated safety net to prevent breaking changes before they reach production.

**3 minutes to set up, saves hours of debugging.**

---

## Setup (One Command)

```powershell
# 1. Install git hooks (runs automatically on every commit)
pwsh scripts/setup-git-hooks.ps1

# 2. Done! Pre-start checks already integrated into "Start All" task
```

---

## What You Get

### Before Every Commit (< 5s)
- ✅ Lint check (ruff)
- ✅ Format check (ruff)
- ✅ Secret detection
- ✅ File hygiene

### Before Every Start (< 15s)
- ✅ Import validation
- ✅ Critical unit tests
- ✅ Config validation

### Before Every Merge (CI)
- ✅ Full test suite
- ✅ Docker build
- ✅ Integration tests

---

## Test Now

```powershell
# Run pre-commit hooks manually
pre-commit run --all-files

# Run pre-start checks manually
pwsh scripts/pre-start-checks.ps1

# Quick mode (skip tests, < 5s)
pwsh scripts/pre-start-checks.ps1 -Quick
```

---

## Full Documentation

See [22-QUALITY-GATE-SYSTEM.md](22-QUALITY-GATE-SYSTEM.md)
