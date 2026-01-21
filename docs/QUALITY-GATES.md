# 🛡️ Quality Gates & Auto-Fix System

## Overview

Yonca AI implements a comprehensive quality gate system that **automatically fixes** most issues before they block your workflow. This document explains how it works and how to use it effectively.

---

## 📋 Table of Contents

1. [Pre-Start Quality Checks](#pre-start-quality-checks)
2. [Git Pre-Commit Hooks](#git-pre-commit-hooks)
3. [Auto-Fix Capabilities](#auto-fix-capabilities)
4. [Manual Fixes](#manual-fixes)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Pre-Start Quality Checks

### What It Does

Before starting services, the system runs fast quality checks:

1. **🔍 Ruff Linting** (< 2s) — **AUTO-FIXES** type annotations, formatting, imports
2. **✅ Import Validation** (< 1s) — Ensures core modules import correctly
3. **🧪 Critical Unit Tests** (< 10s) — Runs essential tests
4. **⚙️ Config Validation** (< 1s) — Validates environment configuration

### Usage

```powershell
# Full checks (default)
pwsh scripts/pre-start-checks.ps1

# Quick mode (skip tests)
pwsh scripts/pre-start-checks.ps1 -Quick

# Disable auto-fix (manual control)
pwsh scripts/pre-start-checks.ps1 -NoAutoFix

# Verbose output
pwsh scripts/pre-start-checks.ps1 -Verbose
```

### Auto-Fix Behavior

When Ruff detects issues, the system:

1. **Attempts automatic fix** using `ruff check --fix --unsafe-fixes`
2. **Re-runs check** to verify all issues resolved
3. **Reports remaining issues** if manual intervention needed

**Example Output:**
```
[1] 🔍 Ruff linting... ❌ FAILED

🔧 Attempting automatic fixes (including unsafe modernizations)...
✅ Auto-fixed all issues!
```

---

## 🪝 Git Pre-Commit Hooks

### Installation

Run once to set up:

```powershell
pwsh scripts/setup-git-hooks.ps1

# Or with initial check on all files
pwsh scripts/setup-git-hooks.ps1 -CheckAll
```

### What Gets Checked

Every commit automatically runs:

- **🔍 Ruff Linter** — Code quality (with --fix enabled)
- **🎨 Ruff Format** — Code formatting
- **🧹 File Hygiene** — Trailing whitespace, EOF newlines
- **✅ File Validation** — YAML, JSON, TOML syntax
- **🚫 Safety Checks** — Large files, merge conflicts
- **🔐 Secret Detection** — Prevent credential leaks

### Bypass Hooks (Emergency Only)

```bash
# Skip hooks temporarily (NOT RECOMMENDED)
git commit --no-verify -m "Emergency fix"
```

---

## 🔧 Auto-Fix Capabilities

### Automatically Fixed

These issues are **automatically resolved** without manual intervention:

| Code | Issue | Auto-Fix | Example |
|------|-------|----------|---------|
| **UP007** | Old-style type hints | ✅ Yes | `Union[str, None]` → `str \| None` |
| **I001** | Unsorted imports | ✅ Yes | Alphabetizes import statements |
| **W291** | Trailing whitespace | ✅ Yes | Removes spaces at line ends |
| **W292** | No newline at EOF | ✅ Yes | Adds final newline |
| **E501** | Line too long | ✅ Yes | Wraps long lines (when safe) |
| **F401** | Unused imports | ✅ Yes | Removes unused imports |

### Requires Manual Fix

These issues **require human judgment**:

| Code | Issue | Why Manual? | How to Fix |
|------|-------|-------------|------------|
| **F841** | Unused variable | Could be needed later | Remove or prefix with `_` |
| **E722** | Bare `except:` | Need to specify exception | Add `Exception` type |
| **B008** | Mutable default arg | Logic change needed | Use `None` + `or` pattern |

---

## 🛠️ Manual Fixes

### F841: Unused Variables

```python
# ❌ Problem
def process(data):
    user_input = data.get("input")  # F841: assigned but never used
    return calculate()

# ✅ Solution 1: Remove if truly unused
def process(data):
    return calculate()

# ✅ Solution 2: Prefix with _ if intentionally unused
def process(data):
    _user_input = data.get("input")  # Signal "unused but intentional"
    return calculate()
```

### E722: Bare Except

```python
# ❌ Problem
try:
    risky_operation()
except:  # E722: bare except
    pass

# ✅ Solution: Specify exception type
try:
    risky_operation()
except Exception:  # Catches all exceptions explicitly
    pass

# ✅ Better: Catch specific exceptions
try:
    risky_operation()
except (ValueError, KeyError) as e:
    logger.warning(f"Expected error: {e}")
```

### Running Manual Fixes

```powershell
# Fix all auto-fixable issues
.venv/Scripts/ruff.exe check src/ tests/ --fix --unsafe-fixes

# Show what would be fixed (dry run)
.venv/Scripts/ruff.exe check src/ tests/ --fix --diff

# Fix specific file
.venv/Scripts/ruff.exe check src/yonca/agent/nodes/agronomist.py --fix
```

---

## ⚙️ Configuration

### Ruff Configuration

Located in [pyproject.toml](../pyproject.toml):

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "UP",  # pyupgrade (modernization)
    "I",   # isort (import sorting)
]

# Add rules to ignore
ignore = [
    # "UP007",  # Uncomment to disable Union → | conversion
]
```

### Pre-Commit Configuration

Located in [.pre-commit-config.yaml](../.pre-commit-config.yaml):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### Disable Auto-Fix Globally

```powershell
# In .venv activation
$env:YONCA_NO_AUTO_FIX = "true"

# Or in scripts/pre-start-checks.ps1
# Add: [switch]$NoAutoFix = $true  # to defaults
```

---

## 🔍 Troubleshooting

### "Auto-fix didn't resolve all issues"

**Cause:** Some issues require manual intervention (F841, E722, etc.)

**Solution:**
1. Read the error messages carefully
2. Refer to [Manual Fixes](#manual-fixes) section
3. Run `ruff check src/ --fix` to see what's left
4. Fix remaining issues one by one

### "Pre-commit hook blocked my commit"

**Cause:** Code quality issues detected

**Solution:**
```bash
# See what failed
pre-commit run --all-files

# Let pre-commit auto-fix
git add -u  # Stage all changes
git commit -m "Your message"  # Hooks run again

# If still failing, check output for manual fixes needed
```

### "Check is too slow"

**Cause:** Running all tests can take 10+ seconds

**Solution:**
```powershell
# Use Quick mode (skip tests)
pwsh scripts/pre-start-checks.ps1 -Quick

# Or update .vscode/tasks.json to use -Quick by default
```

### "False positives on UP007"

**Cause:** Project requires Python < 3.10 (where `X | Y` isn't supported)

**Solution:**
```toml
# In pyproject.toml
[tool.ruff.lint]
ignore = ["UP007"]  # Disable Union → | modernization
```

---

## 📊 Quality Metrics

After setup, you should see:

- **Pre-commit success rate:** > 95% (most issues auto-fixed)
- **Pre-start checks:** < 10s for full checks, < 3s for Quick mode
- **Manual interventions:** < 5% of commits

---

## 🎯 Best Practices

### Development Workflow

1. **Code normally** — Don't worry about perfect formatting
2. **Commit often** — Hooks auto-fix on each commit
3. **Review auto-fixes** — Check what changed before pushing
4. **Run pre-checks** — Before starting services (automatic via tasks)

### When to Skip Auto-Fix

- **Never** — Unless debugging the auto-fix system itself
- **Emergency hotfixes** — Use `--no-verify` sparingly
- **Legacy code** — Consider fixing incrementally

### CI/CD Integration

Pre-commit hooks run locally. For CI:

```yaml
# .github/workflows/quality.yml
- name: Run quality checks
  run: |
    pwsh scripts/pre-start-checks.ps1 -NoAutoFix
```

---

## 🔗 Related Documentation

- [QUALITY-GATE-README.md](../QUALITY-GATE-README.md) — Overview
- [COMMANDS.md](../COMMANDS.md) — All available commands
- [pyproject.toml](../pyproject.toml) — Ruff configuration
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) — Hook configuration

---

## 📝 Summary

The auto-fix system:

✅ **Saves time** — Automatically resolves 95%+ of linting issues
✅ **Prevents errors** — Catches issues before they reach production
✅ **Improves code** — Modernizes to Python 3.10+ best practices
✅ **Educates** — Shows what was fixed in commit diffs

**You write code. The system makes it better. Automatically.**
