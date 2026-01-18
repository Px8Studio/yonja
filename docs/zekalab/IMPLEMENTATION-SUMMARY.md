# Language Interference Fix - Implementation Summary

## What Was Done

### ✅ Analysis
The advice about Turkish language leakage is **highly relevant** and **critical** for Yonca AI:

1. **Problem Confirmed**: Azerbaijani-Turkish linguistic proximity causes models to "leak" Turkish vocabulary
2. **Your Current Setup**: Using `qwen3:4b` (local) and `llama-3.1-8b-instant` (cloud) - both susceptible
3. **Solution Provided**: Dual-model strategy + enhanced system prompts with linguistic anchors

---

## ✅ Files Created/Modified

### 1. Enhanced System Prompt
**File**: `prompts/system/master_v1.0.0_az_strict.txt`

**Features**:
- ✅ Explicit linguistic anchors (correct Azerbaijani words)
- ❌ Negative constraints (forbidden Turkish words)
- 📋 Quality self-check before responding
- 📚 Russian-origin month names (Sentyabr, Oktyabr, etc.)

**Key Sections**:
```
<DİL_QAYDALARI>
QADAĞAN EDİLMİŞ TÜRK SÖZLƏRİ:
❌ eylül → ✅ Sentyabr
❌ zemin → ✅ torpaq
❌ sulama → ✅ suvarma
...
</DİL_QAYDALARI>
```

### 2. Model Role Configuration
**File**: `src/yonca/llm/model_roles.py`

**Defines**:
- Model capabilities and roles (chat vs reasoning)
- LangGraph node → model mappings
- System prompt strategies per model
- Helper functions for model selection

**Key Functions**:
```python
get_model_for_node("response_writer", "cloud")  # → llama-3.3-70b-versatile
get_model_for_node("irrigation_calculator", "cloud")  # → qwen3-32b
should_rewrite_response("qwen3-32b")  # → True
```

### 3. Reasoning Node Prompt
**File**: `prompts/system/reasoning_node.txt`

**Purpose**: Stripped-down prompt for internal Qwen calculations (output hidden from user)

### 4. Updated Chat Endpoint
**File**: `src/yonca/api/routes/chat.py`

**Changes**:
- Added `load_system_prompt()` function
- Loads enhanced prompt from file
- Fallback to basic prompt if file missing

### 5. Updated Default Config
**File**: `src/yonca/config.py`

**Changed**:
```python
# OLD
groq_model: str = "llama-3.1-8b-instant"

# NEW (Better Azerbaijani quality)
groq_model: str = "llama-3.3-70b-versatile"
```

### 6. Documentation
**Files**:
- `docs/zekalab/LANGUAGE-INTERFERENCE-GUIDE.md` - Complete guide
- `docs/zekalab/MODEL-SELECTION-QUICK-REF.md` - Quick reference

### 7. Test Script
**File**: `scripts/test_language_quality.ps1`

Automated testing for Turkish leakage detection.

---

## 🎯 Recommended Strategy

### Dual-Model Approach

```
┌─────────────────────────────────────────────────┐
│          YONCA AI ARCHITECTURE                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────┐      ┌───────────────┐      │
│  │  REASONING    │      │   LANGUAGE    │      │
│  │   (Qwen)      │ ───> │   (Llama)     │      │
│  │               │      │               │      │
│  │ • Math/Logic  │      │ • Azerbaijani │      │
│  │ • Calculation │      │ • Conversation│      │
│  │ • Internal    │      │ • User-facing │      │
│  └───────────────┘      └───────────────┘      │
│                                                 │
│  ┌─────────────────────────────────────┐       │
│  │  OFFLINE (ATLLaMA)                  │       │
│  │  • Fine-tuned Azerbaijani           │       │
│  │  • Zero Turkish leakage             │       │
│  └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

### Model Selection Rules

**Cloud Mode (Groq)**:
- User-facing responses → `llama-3.3-70b-versatile`
- Internal calculations → `qwen3-32b`

**Local Mode (Ollama)**:
- User-facing responses → `atllama` (ALWAYS)
- Internal calculations → `qwen3:4b` (then rewrite with atllama)

---

## 🧪 Testing

### Run Language Quality Tests
```powershell
# Test both providers
.\scripts\test_language_quality.ps1 -Provider both

# Test Groq only (requires API key)
.\scripts\test_language_quality.ps1 -Provider groq -GroqApiKey "gsk_your_key"

# Test Ollama only (requires running Ollama with atllama)
.\scripts\test_language_quality.ps1 -Provider ollama
```

### Manual Testing Checklist
Test with: **"Buğda əkmək üçün ən yaxşı vaxt nədir?"**

Expected (Azerbaijani):
- ✅ "Sentyabr" (not "Eylül")
- ✅ "torpaq" (not "zemin")
- ✅ "suvarma" (not "sulama")

---

## 📋 Next Steps

### Immediate (Can do now)
1. **Set environment variable**:
   ```powershell
   $env:YONCA_GROQ_MODEL = "llama-3.3-70b-versatile"
   ```

2. **Test with Groq** (if you have API key):
   ```powershell
   .\scripts\test_language_quality.ps1 -Provider groq
   ```

3. **Test with Ollama**:
   ```powershell
   # Make sure Ollama is running with atllama model
   docker exec yonca-ollama ollama list  # Check if atllama exists
   .\scripts\test_language_quality.ps1 -Provider ollama
   ```

### Short-term (This week)
1. Implement LangGraph with dual-model strategy
2. Create rewriting pipeline (Qwen → Llama/ATLLaMA)
3. Add intent detection for model routing

### Medium-term (This month)
1. Collect real farmer conversations
2. Build Azerbaijani evaluation dataset
3. Monitor Turkish leakage in production
4. Fine-tune prompts based on feedback

---

## 🎓 Key Learnings from the Advice

### What the Advisor Got Right
1. ✅ **Language Interference is Real** - Turkish words do leak into Azerbaijani
2. ✅ **Model Strengths Differ** - Qwen = math, Llama = language
3. ✅ **Dual Strategy Works** - Use different models for different purposes
4. ✅ **System Prompt Anchoring** - Negative constraints reduce leakage
5. ✅ **ATLLaMA is Superior** - Fine-tuned specifically for Azerbaijani

### How We Applied It
1. Created enhanced system prompt with linguistic anchors
2. Defined model roles and capabilities
3. Built infrastructure for dual-model LangGraph
4. Updated defaults to better models
5. Created testing framework

---

## 📊 Model Comparison (2026)

| Model | Provider | Azerbaijani | Math | Speed | Use For |
|:------|:---------|:-----------|:-----|:------|:--------|
| llama-3.3-70b-versatile | Groq | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚡⚡⚡ | Chat (cloud) |
| qwen3-32b | Groq | ⭐⭐ ⚠️ | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | Calculations (hidden) |
| atllama | Ollama | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⚡ | Chat (offline) |
| qwen3:4b | Ollama | ⭐⭐ ⚠️ | ⭐⭐⭐⭐ | ⚡⚡ | Calculations (local) |

⚠️ = Turkish leakage risk

---

## 🔗 Related Files

- System Prompts: [prompts/system/](../prompts/system/)
- Model Roles: [src/yonca/llm/model_roles.py](../src/yonca/llm/model_roles.py)
- Chat Endpoint: [src/yonca/api/routes/chat.py](../src/yonca/api/routes/chat.py)
- Config: [src/yonca/config.py](../src/yonca/config.py)
- Full Guide: [docs/zekalab/LANGUAGE-INTERFERENCE-GUIDE.md](./LANGUAGE-INTERFERENCE-GUIDE.md)
- Quick Ref: [docs/zekalab/MODEL-SELECTION-QUICK-REF.md](./MODEL-SELECTION-QUICK-REF.md)
- Test Script: [scripts/test_language_quality.ps1](../scripts/test_language_quality.ps1)

---

## ✅ Status: READY FOR TESTING

All infrastructure is in place. You can now:
1. Run language quality tests
2. Deploy with improved model defaults
3. Build LangGraph with dual-model strategy

**The advisor's template offer has been pre-implemented** in `prompts/system/master_v1.0.0_az_strict.txt`!
