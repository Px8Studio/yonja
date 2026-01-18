# 🇦🇿 Language Interference Prevention Guide

## The Problem: Turkish Language Leakage

**Background:**  
Azerbaijani and Turkish are linguistically similar. Many general-purpose LLMs trained on Turkish data "leak" Turkish vocabulary when generating Azerbaijani text, especially when uncertain about word choice.

### Common Interference Examples

| Turkish (❌ Wrong) | Azerbaijani (✅ Correct) | Context |
|:------------------|:------------------------|:--------|
| eylül | Sentyabr | September month name |
| zemin | torpaq | Soil/ground |
| sulama | suvarma | Irrigation |
| ekim | əkin | Planting/sowing |
| tohum | toxum | Seed |
| ürün | məhsul | Crop/product |
| hayır | xeyr | No |
| tarla | tarla | Field (same, but watch context) |

### Real Example from Testing

**User:** "Buğda əkmək üçün ən yaxşı vaxt nədir?"

**❌ Bad Response (Turkish leakage):**
> "Buğday ekimi için en iyi zaman **Eylül** ayıdır. **Zemin** hazırlığı yapmalısınız..."

**✅ Good Response (Pure Azerbaijani):**
> "Buğda əkini üçün ən yaxşı vaxt **Sentyabr** və **Oktyabr** aylarıdır. **Torpağı** əvvəlcədən hazırlamaq lazımdır..."

---

## Our Solution: Dual-Model Strategy

Different models excel at different tasks. We use role-based model selection:

### Model Roles

```
┌─────────────────────────────────────────────────┐
│          YONCA AI MODEL ARCHITECTURE            │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────┐      ┌───────────────┐      │
│  │  REASONING    │      │   LANGUAGE    │      │
│  │   (Qwen)      │ ───> │   (Llama)     │      │
│  │               │      │               │      │
│  │ • Math/Logic  │      │ • Azerbaijani │      │
│  │ • Calculation │      │ • Conversation│      │
│  │ • Hidden from │      │ • User-facing │      │
│  │   user        │      │               │      │
│  └───────────────┘      └───────────────┘      │
│                                                 │
│  ┌─────────────────────────────────────┐       │
│  │  OFFLINE FALLBACK (ATLLaMA)         │       │
│  │  • Fine-tuned for Azerbaijani       │       │
│  │  • No Turkish leakage               │       │
│  │  • Slower but highest quality       │       │
│  └─────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

### Model Selection Logic

**1. Cloud Mode (Groq API available):**
- **Reasoning Nodes** (irrigation calc, fertilization, etc.) → `qwen3-32b`
  - Superior math/logic capabilities
  - Output is hidden, will be rewritten
- **Language Nodes** (chat, response generation) → `llama-3.3-70b-versatile`
  - Better multilingual balance
  - Less Turkish leakage
  - User-facing output

**2. Local Mode (Offline/No API key):**
- **Reasoning Nodes** → `qwen3:4b`
- **Language Nodes** → `atllama`
  - Fine-tuned specifically for Azerbaijani
  - Best language quality
  - **Always** use for final farmer-facing responses

---

## Implementation

### 1. Enhanced System Prompt

Located in: `prompts/system/master_v1.0.0_az_strict.txt`

**Key Features:**
- ✅ **Linguistic Anchors**: Explicit list of correct Azerbaijani words
- ❌ **Negative Constraints**: Forbidden Turkish words
- 📋 **Quality Checklist**: Self-validation before responding
- 📚 **Month Names**: Russian-origin names (Sentyabr, Oktyabr, etc.)

**Example Section:**
```
<DİL_QAYDALARI>
⚠️ KRİTİK: Yalnız Azərbaycan dilində danış. Türk dilindən sözləri QƏTI QADAĞANDIR.

QADAĞAN EDİLMİŞ TÜRK SÖZLƏRİ:
❌ eylül → ✅ Sentyabr
❌ zemin → ✅ torpaq
❌ sulama → ✅ suvarma
...
</DİL_QAYDALARI>
```

### 2. Model Role Configuration

Located in: `src/yonca/llm/model_roles.py`

**Key Components:**
```python
MODEL_ROLES = {
    "llama-3.3-70b-versatile": {
        "role": "chat",
        "azerbaijani_quality": "high",
        "use_for": ["final_response_generation", "farmer_conversation"]
    },
    "qwen3-32b": {
        "role": "reasoning",
        "azerbaijani_quality": "medium",  # Turkish leakage risk
        "use_for": ["calculations", "internal_reasoning_nodes"]
    },
    "atllama": {
        "role": "offline_expert",
        "azerbaijani_quality": "very_high",  # Fine-tuned
        "use_for": ["offline_mode", "final_response_when_local"]
    }
}
```

**Helper Functions:**
```python
# Get model for a specific LangGraph node
get_model_for_node("response_writer", "cloud")  # → llama-3.3-70b-versatile
get_model_for_node("response_writer", "local")  # → atllama

# Check if rewriting needed
should_rewrite_response("qwen3-32b")  # → True (rewrite with Llama/ATLLaMA)
should_rewrite_response("llama-3.3-70b-versatile")  # → False (already good)
```

### 3. Updated Chat Endpoint

Located in: `src/yonca/api/routes/chat.py`

Now loads enhanced system prompt:
```python
def load_system_prompt(prompt_name: str = "master_v1.0.0_az_strict") -> str:
    """Load system prompt from file with linguistic anchors."""
    # Loads from prompts/system/master_v1.0.0_az_strict.txt
    ...

SYSTEM_PROMPT_AZ = load_system_prompt("master_v1.0.0_az_strict")
```

---

## Testing Protocol

### Test Cases

#### 1. Basic Language Test
**Prompt:**
```
Salam! Buğda əkmək üçün ən yaxşı vaxt nədir?
```

**Expected (Azerbaijani):**
- ✅ "Sentyabr və Oktyabr"
- ✅ "torpaq"
- ✅ "suvarma"

**Forbidden (Turkish):**
- ❌ "Eylül"
- ❌ "zemin"
- ❌ "sulama"

#### 2. Multi-Turn Conversation
**Turn 1:**
```
Pomidor əkmək istəyirəm. Nə vaxt əkməliyəm?
```

**Turn 2:**
```
Torpaq necə olmalıdır?
```

**Validation:**
- Check all month names are Russian-origin
- Check all agricultural terms are Azerbaijani
- No Turkish vocabulary in any turn

#### 3. Edge Case: Turkish Input
**User writes in Turkish:**
```
Domates ekmek istiyorum. Ne zaman ekmeliyim?
```

**Expected Response:**
- Respond in Azerbaijani (not Turkish)
- Politely explain: "Mən yalnız Azərbaycan dilində cavab verirəm"

### PowerShell Test Script

```powershell
# Test with enhanced system prompt
$headers = @{ 
    "Authorization" = "Bearer $env:YONCA_GROQ_API_KEY"
    "Content-Type" = "application/json" 
}

# Read the enhanced system prompt
$systemPrompt = Get-Content "prompts/system/master_v1.0.0_az_strict.txt" -Raw

$body = @{
    model = "llama-3.3-70b-versatile"
    messages = @(
        @{
            role = "system"
            content = $systemPrompt
        },
        @{
            role = "user"
            content = "Buğda əkmək üçün ən yaxşı vaxt nədir?"
        }
    )
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod `
    -Uri "https://api.groq.com/openai/v1/chat/completions" `
    -Method Post `
    -Headers $headers `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))

$response.choices[0].message.content
```

### Quality Checklist

After each response, verify:
- [ ] All month names use Russian-origin format (Sentyabr, not Eylül)
- [ ] "torpaq" used (not "zemin")
- [ ] "suvarma" used (not "sulama")
- [ ] "toxum" used (not "tohum")
- [ ] "məhsul" used (not "ürün")
- [ ] No other Turkish vocabulary detected
- [ ] Response is helpful and contextually appropriate

---

## Future: LangGraph Integration

When implementing LangGraph nodes:

### Example Workflow

```python
# Node 1: Calculate irrigation schedule (Qwen for math)
irrigation_plan = await qwen_node.calculate({
    "hectares": 50,
    "crop": "wheat",
    "soil_type": "clay"
})
# Output: {"schedule": [...], "water_liters": 50000, ...}
# (May contain Turkish words - doesn't matter, hidden from user)

# Node 2: Rewrite in perfect Azerbaijani (Llama for language)
final_response = await llama_node.rewrite({
    "raw_plan": irrigation_plan,
    "target_language": "azerbaijani",
    "tone": "friendly_farmer"
})
# Output: Pure Azerbaijani text shown to farmer
```

### Node Configuration

```python
from yonca.llm.model_roles import get_model_for_node, LANGGRAPH_NODE_MODELS

# Get models for cloud deployment
nodes = LANGGRAPH_NODE_MODELS["cloud"]
# {
#     "supervisor": "llama-3.3-70b-versatile",
#     "irrigation_calculator": "qwen3-32b",
#     "response_writer": "llama-3.3-70b-versatile",
#     ...
# }

# Or for local deployment
nodes = LANGGRAPH_NODE_MODELS["local"]
# {
#     "supervisor": "atllama",
#     "irrigation_calculator": "qwen3:4b",
#     "response_writer": "atllama",  # Always ATLLaMA for final output
#     ...
# }
```

---

## Recommendations

### 1. Accept the Advice ✅

The advisor's recommendations are **highly relevant** and align with your architecture goals:

- ✅ Use Llama 3.3 70B for user-facing chat (cloud mode)
- ✅ Use Qwen for internal reasoning/calculations
- ✅ Always use ATLLaMA for offline mode
- ✅ Implement strict linguistic anchors in system prompts

### 2. Priority Actions

**Immediate (Done):**
- [x] Enhanced system prompt with negative constraints
- [x] Model role configuration
- [x] Update chat endpoint to load new prompts

**Next Steps:**
1. Test with Groq API using `llama-3.3-70b-versatile`
2. Run language quality tests (see Testing Protocol)
3. Implement LangGraph with dual-model strategy
4. Add response rewriting pipeline

**Future:**
1. Collect real farmer conversations
2. Build Azerbaijani-specific evaluation dataset
3. Fine-tune local model if needed
4. Monitor for Turkish leakage in production

### 3. Configuration Changes

**Update `.env` file:**
```bash
# Use Llama for better Azerbaijani quality
YONCA_GROQ_MODEL=llama-3.3-70b-versatile

# Keep Qwen for local reasoning
YONCA_OLLAMA_MODEL=qwen3:4b
```

**For offline mode:**
```bash
YONCA_LLM_PROVIDER=ollama
YONCA_OLLAMA_MODEL=atllama  # Best Azerbaijani quality
```

---

## References

- Enhanced System Prompt: [prompts/system/master_v1.0.0_az_strict.txt](../prompts/system/master_v1.0.0_az_strict.txt)
- Model Roles Config: [src/yonca/llm/model_roles.py](../src/yonca/llm/model_roles.py)
- Reasoning Prompt: [prompts/system/reasoning_node.txt](../prompts/system/reasoning_node.txt)
- Updated Chat Endpoint: [src/yonca/api/routes/chat.py](../src/yonca/api/routes/chat.py)

---

## Template Request

The advisor offered a **"System Prompt Master Template"** with negative constraints. 

**Status:** ✅ **Already Created**

We've implemented this as:
- `prompts/system/master_v1.0.0_az_strict.txt` - Full template with linguistic anchors
- Includes forbidden Turkish words list
- Includes quality self-check before responding
- Loaded automatically in chat endpoints

**You can request additional templates from the advisor for:**
- Intent-specific prompts (irrigation, pest control, etc.)
- Few-shot example libraries
- Context injection patterns
