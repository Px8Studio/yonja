# Quick Reference: Model Selection for Yonca AI

## 🏆 The Gold Standard: 70B Parameter Class

> **For national-scale agricultural AI, 70B models are the "Goldilocks zone"**—smart enough for complex agronomic reasoning, efficient enough for high-end local hardware.

### Why 70B Over 8B?

| Capability | 8B Models | 70B Models (Gold Standard) |
|:-----------|:----------|:---------------------------|
| **Reasoning** | Single-step | Multi-step (soil pH + weather + crop stage) |
| **Azerbaijani** | Turkish leakage risk | Strong internal filter |
| **JSON Output** | Inconsistent | Deterministic (API-ready) |
| **Nuanced Intent** | Misses subtle queries | Expert-level understanding |

---

## TL;DR - Which Model to Use?

### Open-Source Mode (Groq - Recommended)
```bash
# Chat with farmers (user-facing) - GOLD STANDARD
llama-3.3-70b-versatile  # ⭐ Best Azerbaijani quality, 70B class

# Internal calculations (hidden)
qwen3-32b  # ⭐ Best math/logic

# Future upgrade path
llama-4-maverick  # When available via Groq
```

### Proprietary Mode (Gemini - Fallback Only)
```bash
# ⚠️ Only use when open-source unavailable
gemini-2.0-flash-exp  # Cannot self-host, vendor lock-in
```

---

## Current Rankings (2026)

### For Azerbaijani Language Quality
1. 🥇 **llama-3.3-70b-versatile** (Groq) - Best multilingual balance
2. 🥈 **llama-3.1-8b-instant** (Groq) - Fast, decent quality
3. 🥉 **mixtral-8x7b-32768** (Groq) - Good alternative
4. ⚠️ **qwen3-32b** (Groq) - Math great, but Turkish leakage risk
5. ⚠️ **gemini-2.0-flash-exp** - Proprietary, cannot self-host

### For Math & Logic
1. 🥇 **qwen3-32b** (Groq) - Superior calculations
2. 🥈 **llama-3.3-70b-versatile** (Groq) - Good all-around
3. 🥉 **gemini-2.0-flash-exp** - Proprietary fallback

---

## Decision Tree

```
Are you deploying to production with real farmers?
│
├─ YES → Use Groq (open-source models)
│   │
│   ├─ User will see this output?
│   │   ├─ YES → llama-3.3-70b-versatile
│   │   └─ NO (internal calculation) → qwen3-32b
│   │
│   └─ Need self-hosting for gov compliance?
│       └─ YES → Deploy vLLM/TGI with same models
│
└─ NO (development/testing)
    │
    └─ Use Groq API (free tier: 14,400 req/day)
        │
        ├─ User will see this output?
        │   └─ YES → llama-3.3-70b-versatile
        │
        └─ NO (internal calculation)
            └─ qwen3-32b, then rewrite with Llama
```

---

## Testing Commands

### Test Groq (Open-Source Models)
```powershell
# Test Llama for language quality
$env:YONCA_LLM_PROVIDER = "groq"
$env:YONCA_GROQ_MODEL = "llama-3.3-70b-versatile"
$env:YONCA_GROQ_API_KEY = "gsk_your_key_here"

# Start API and test
# Should respond in pure Azerbaijani, no Turkish words
```

### Test Self-Hosted (Production)
```powershell
# Point to your vLLM/TGI server
$env:YONCA_LLM_PROVIDER = "groq"
$env:YONCA_GROQ_BASE_URL = "http://your-llm-cluster:8000"
$env:YONCA_GROQ_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

# Same API, same code - just local
```

---

## Configuration Examples

### Recommended Production Config (.env)
```bash
# Open-Source Mode (Recommended)
YONCA_DEPLOYMENT_MODE=open_source
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.3-70b-versatile
YONCA_GROQ_API_KEY=gsk_your_key_here

# For self-hosted production:
# YONCA_GROQ_BASE_URL=http://your-llm-cluster:8000
```

### Development Config (Groq free tier)
```bash
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.3-70b-versatile
YONCA_GROQ_API_KEY=gsk_your_key_here
# Free tier: 14,400 requests/day
```

### Fast Testing Config
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
   YONCA_LLM_PROVIDER=groq
   YONCA_GROQ_MODEL=llama-3.3-70b-versatile
   YONCA_GROQ_API_KEY=gsk_your_key_here
   ```

2. **Test the model:**
   ```bash
   # Restart API server
   # Send test message: "Buğda əkmək üçün ən yaxşı vaxt nədir?"
   # Verify: No "eylül", "zemin", or other Turkish words
   ```

3. **When building LangGraph:**
   - Use `get_model_for_node()` helper from `model_roles.py`
   - Reasoning nodes → Qwen (math/logic)
   - Chat nodes → Llama (Azerbaijani quality)

4. **For production (government compliance):**
   - Deploy vLLM or TGI on-premises
   - Point `YONCA_GROQ_BASE_URL` to your cluster
   - Same models, full data control

---

## Why Open-Source?

| Benefit | Description |
|:--------|:------------|
| **Self-Hosting** | Deploy same models on your own infrastructure |
| **No Vendor Lock-in** | Switch providers anytime, no code changes |
| **Data Privacy** | Keep all data on-premises for government compliance |
| **Cost Control** | One-time hardware investment vs per-token pricing |
| **Customization** | Fine-tune models on Azerbaijani agricultural data |

---

## Hardware Quick Reference

### For 70B Gold Standard Models

| Option | Hardware | VRAM | Cost | Performance |
|:-------|:---------|:-----|:-----|:------------|
| **Workstation** | 2× RTX 5090 | 64GB | ~$6,500 | 15-20 tok/s |
| **Mac Studio** | M3/M4 Ultra | 128GB Unified | ~$4,800 | 10-15 tok/s |
| **AzInCloud** | NVIDIA H100 | 80GB | €2.80/hr | 50-100 tok/s |

> 💡 **Break-even vs cloud APIs: ~5 months** — See [15-HARDWARE-JUSTIFICATION.md](15-HARDWARE-JUSTIFICATION.md) for full economics.

---

## Support

Questions? Check:
- **Hardware Economics**: [15-HARDWARE-JUSTIFICATION.md](15-HARDWARE-JUSTIFICATION.md)
- Full guide: [LANGUAGE-INTERFERENCE-GUIDE.md](LANGUAGE-INTERFERENCE-GUIDE.md)
- Deployment: [12-DUAL-MODE-DEPLOYMENT.md](12-DUAL-MODE-DEPLOYMENT.md)
- Model config: [src/yonca/llm/model_roles.py](../../src/yonca/llm/model_roles.py)
- System prompts: [prompts/system/](../../prompts/system/)
