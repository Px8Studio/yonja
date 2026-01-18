# Quick Reference: Model Selection for Yonca AI

## TL;DR - Which Model to Use?

### Cloud Mode (Groq)
```bash
# Chat with farmers (user-facing)
llama-3.3-70b-versatile  # ⭐ Best Azerbaijani quality

# Internal calculations (hidden)
qwen3-32b  # ⭐ Best math/logic
```

### Local Mode (Ollama)
```bash
# Chat with farmers
atllama  # ⭐ Fine-tuned for Azerbaijani, no Turkish leakage

# Internal calculations
qwen3:4b  # Good math, but rewrite output with atllama
```

---

## Current Rankings (2026)

### For Azerbaijani Language Quality
1. 🥇 **atllama** (local) - Fine-tuned, zero Turkish leakage
2. 🥈 **llama-3.3-70b-versatile** (Groq) - Balanced multilingual
3. 🥉 **llama-3.1-8b-instant** (Groq) - Fast, decent quality
4. ⚠️ **qwen3-32b** (Groq) - Math great, language has Turkish leakage
5. ⚠️ **qwen3:4b** (local) - Same as above, smaller

### For Math & Logic
1. 🥇 **qwen3-32b** (Groq) - Superior calculations
2. 🥈 **qwen3:4b** (local) - Good for local
3. 🥉 **llama-3.3-70b-versatile** (Groq) - Decent
4. **atllama** (local) - Basic math only

---

## Decision Tree

```
Are you deploying to production with real farmers?
│
├─ YES → Use Groq (cloud)
│   │
│   ├─ User will see this output?
│   │   ├─ YES → llama-3.3-70b-versatile
│   │   └─ NO (internal calculation) → qwen3-32b
│   │
│   └─ Fallback if Groq down → atllama (local)
│
└─ NO (development/testing/offline)
    │
    └─ Use Ollama (local)
        │
        ├─ User will see this output?
        │   └─ YES → atllama (always!)
        │
        └─ NO (internal calculation)
            └─ qwen3:4b, then rewrite with atllama
```

---

## Testing Commands

### Test Groq (Cloud)
```powershell
# Test Llama for language quality
$env:YONCA_LLM_PROVIDER = "groq"
$env:YONCA_GROQ_MODEL = "llama-3.3-70b-versatile"
$env:YONCA_GROQ_API_KEY = "gsk_your_key_here"

# Start API and test
# Should respond in pure Azerbaijani, no Turkish words
```

### Test Ollama (Local)
```powershell
# Test ATLLaMA for offline quality
$env:YONCA_LLM_PROVIDER = "ollama"
$env:YONCA_OLLAMA_MODEL = "atllama"

# Start API and test
# Slower, but best Azerbaijani quality
```

---

## Configuration Examples

### Recommended Production Config (.env)
```bash
# Primary provider (cloud for speed)
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.3-70b-versatile  # Changed from llama-3.1-8b-instant
YONCA_GROQ_API_KEY=gsk_your_key_here

# Fallback provider (local for offline)
YONCA_OLLAMA_BASE_URL=http://localhost:11434
YONCA_OLLAMA_MODEL=atllama  # Changed from qwen3:4b
```

### Development Config (local only)
```bash
YONCA_LLM_PROVIDER=ollama
YONCA_OLLAMA_MODEL=atllama
YONCA_OLLAMA_BASE_URL=http://localhost:11434
```

### Testing Config (fastest)
```bash
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.1-8b-instant  # Fast but lower quality
YONCA_GROQ_API_KEY=gsk_your_key_here
```

---

## Common Mistakes to Avoid

### ❌ Don't Do This
```python
# Using Qwen for farmer-facing chat
messages = [
    LLMMessage.system(SYSTEM_PROMPT),
    LLMMessage.user("Buğda nə vaxt əkilir?")
]
response = qwen.generate(messages)  # ❌ May contain Turkish words!
return response.content  # ❌ Showing to farmer directly
```

### ✅ Do This Instead
```python
# Option 1: Use Llama for chat
response = llama.generate(messages)  # ✅ Better Azerbaijani
return response.content

# Option 2: Calculate with Qwen, rewrite with Llama
calculation = qwen.generate(calc_messages)  # Internal, hidden
final = llama.generate([
    LLMMessage.system("Rewrite this in perfect Azerbaijani"),
    LLMMessage.user(calculation.content)
])  # ✅ Clean output
return final.content
```

---

## Groq Model Availability (January 2026)

| Model | Speed | Quality | Azerbaijani | Math | Context |
|:------|:------|:--------|:------------|:-----|:--------|
| llama-3.3-70b-versatile | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 128k |
| llama-3.1-8b-instant | ⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 8k |
| qwen3-32b | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐ ⚠️ | ⭐⭐⭐⭐⭐ | 32k |
| mixtral-8x7b-32768 | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 32k |

⚠️ = Turkish leakage risk

---

## Performance Benchmarks

```
Typical Response Times (tested January 2026):
─────────────────────────────────────────────

Groq (llama-3.3-70b-versatile):
  • 500 token response: ~2.5 seconds
  • Tokens/second: 200-250

Groq (qwen3-32b):
  • 500 token response: ~1.8 seconds
  • Tokens/second: 250-300

Ollama (atllama) on CPU (i7-12th gen):
  • 500 token response: ~45 seconds
  • Tokens/second: 10-12

Ollama (atllama) on GPU (RTX 4060):
  • 500 token response: ~8 seconds
  • Tokens/second: 60-70
```

---

## Next Steps

1. **Update your .env:**
   ```bash
   YONCA_GROQ_MODEL=llama-3.3-70b-versatile
   ```

2. **Test the new model:**
   ```bash
   # Restart API server
   # Send test message: "Buğda əkmək üçün ən yaxşı vaxt nədir?"
   # Verify: No "eylül", "zemin", or other Turkish words
   ```

3. **When building LangGraph:**
   - Use `get_model_for_node()` helper from `model_roles.py`
   - Reasoning nodes → Qwen
   - Chat nodes → Llama/ATLLaMA

4. **Monitor production:**
   - Log all responses
   - Flag Turkish word occurrences
   - Collect farmer feedback on language quality

---

## Support

Questions? Check:
- Full guide: [LANGUAGE-INTERFERENCE-GUIDE.md](LANGUAGE-INTERFERENCE-GUIDE.md)
- Model config: [src/yonca/llm/model_roles.py](../src/yonca/llm/model_roles.py)
- System prompts: [prompts/system/](../prompts/system/)
