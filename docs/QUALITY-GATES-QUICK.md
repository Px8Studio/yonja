# 🚀 Quick Reference: Auto-Fix System

## One-Line Summary
**The quality system automatically fixes 95% of code issues before they block you.**

---

## 🎯 Quick Actions

### Fix All Issues Now
```powershell
.venv/Scripts/ruff.exe check src/ tests/ --fix --unsafe-fixes
```

### Run Pre-Start Checks
```powershell
# Full checks (recommended)
pwsh scripts/pre-start-checks.ps1

# Quick mode (skip tests)
pwsh scripts/pre-start-checks.ps1 -Quick
```

### Setup Git Hooks (One-Time)
```powershell
pwsh scripts/setup-git-hooks.ps1 -CheckAll
```

---

## 📊 What Gets Auto-Fixed

| Issue Type | Auto-Fix | Example |
|------------|----------|---------|
| **Type hints** | ✅ Yes | `Union[str, None]` → `str \| None` |
| **Import sorting** | ✅ Yes | Alphabetizes imports |
| **Whitespace** | ✅ Yes | Removes trailing spaces |
| **Line length** | ✅ Yes | Wraps long lines |
| **Unused imports** | ✅ Yes | Removes automatically |
| **Unused variables** | ❌ Manual | Prefix with `_` or remove |
| **Bare except** | ❌ Manual | Add `Exception` type |

---

## 🛠️ Common Manual Fixes

### Unused Variable (F841)
```python
# Before
user_input = get_input()  # F841

# Fix: Remove or prefix with _
_user_input = get_input()
```

### Bare Except (E722)
```python
# Before
except:  # E722

# Fix
except Exception:
```

---

## 🔧 Workflow

1. **Write code** (don't worry about formatting)
2. **Commit** (hooks auto-fix)
3. **Review changes** (see what was fixed)
4. **Push** (all checks passed!)

---

## 🆘 Emergency Bypass

```bash
# Skip hooks (NOT RECOMMENDED)
git commit --no-verify -m "Emergency fix"

# Disable auto-fix temporarily
pwsh scripts/pre-start-checks.ps1 -NoAutoFix
```

---

## 📖 Full Documentation

See [docs/QUALITY-GATES.md](./QUALITY-GATES.md) for complete guide.
