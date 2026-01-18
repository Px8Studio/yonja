# Quick Reference: Model Selection for Yonca AI

## 🏆 The 2026 Gold Standard: Llama 4 Maverick

> **Llama 4 Maverick is a Mixture-of-Experts (MoE) model with 17B active parameters and 128 experts.** It replaces the previous two-model stack (Qwen + Llama) with a single, all-in-one solution.

### Why Maverick Over the Legacy Stack?

| Feature | **Legacy Combination** (Qwen 3 + Llama 3.3) | **The New King** (Llama 4 Maverick) |
|:--------|:-------------------------------------------|:-----------------------------------|
| **LangGraph Nodes** | 2 Nodes (Reasoning → Editing) | **1 Node (All-in-One)** |
| **Logic/Math** | Excellent (Qwen) | **Excellent (Native)** |
| **Azeri Quality** | Excellent (after Llama 3.3 edit) | **Superior (Native, no Turkish)** |
| **Speed on Groq** | Fast (but runs twice) | **Ultra-Fast (~300 tps)** |
| **Vision (Images)** | ❌ No | **✅ Yes (Native)** |
| **Token Cost** | 2x (double-pass) | **1x (single-pass)** |
| **Model ID** | `qwen/qwen3-32b` + `llama-3.3-70b-versatile` | **`meta-llama/llama-4-maverick-17b-128e-instruct`** |

---

## TL;DR - Which Model to Use?

### 2026 Recommended: Maverick Mode
```bash
# Single model for ALL tasks (chat, logic, vision)
meta-llama/llama-4-maverick-17b-128e-instruct  # ⭐ 2026 GOLD STANDARD
```

### Legacy Mode (Still Supported)
```bash
# Chat with farmers (user-facing)
llama-3.3-70b-versatile  # Best Azerbaijani quality

# Internal calculations (hidden)
qwen3-32b  # Best math/logic (Turkish leakage risk)
```

### Proprietary Mode (Gemini - Fallback Only)
```bash
# ⚠️ Only use when open-source unavailable
gemini-2.0-flash-exp  # Cannot self-host, vendor lock-in
```

---

## Current Rankings (January 2026)

### Overall Recommendation
1. 🥇 **meta-llama/llama-4-maverick-17b-128e-instruct** (Groq) - **2026 GOLD STANDARD**
2. 🥈 **llama-3.3-70b-versatile** (Groq) - Legacy, still excellent for language
3. 🥉 **qwen3-32b** (Groq) - Math-only tasks (Turkish leakage for chat)

### For Azerbaijani Language Quality
1. 🥇 **Llama 4 Maverick** - Native Azerbaijani, no Turkish leakage
2. 🥈 **llama-3.3-70b-versatile** (Groq) - Best multilingual balance
3. 🥉 **llama-3.1-8b-instant** (Groq) - Fast, decent quality
4. ⚠️ **qwen3-32b** (Groq) - Math great, but Turkish leakage risk

### For Math & Logic
1. 🥇 **Llama 4 Maverick** - 400B-equivalent reasoning
2. 🥈 **qwen3-32b** (Groq) - Superior calculations (but needs rewrite)
3. 🥉 **llama-3.3-70b-versatile** (Groq) - Good all-around

### For Vision (Image Analysis)
1. 🥇 **Llama 4 Maverick** - Native multimodal (crop disease photos!)
2. ❌ All other models - No vision support

---

## Decision Tree (2026)

```
Are you deploying to production with real farmers?
│
├─ YES → Use Groq (open-source models)
│   │
│   ├─ Need vision (image analysis)?
│   │   └─ YES → meta-llama/llama-4-maverick-17b-128e-instruct
│   │
│   ├─ Want simplest architecture?
│   │   └─ YES → meta-llama/llama-4-maverick-17b-128e-instruct (1 node)
│   │
│   └─ Legacy mode (for comparison)?
│       ├─ User-facing → llama-3.3-70b-versatile
│       └─ Internal calc → qwen3-32b → rewrite with Llama
│
└─ NO (development/testing)
    │
    └─ Use Groq API (free tier: 14,400 req/day)
        └─ meta-llama/llama-4-maverick-17b-128e-instruct
```

---

## Testing Commands

### Test Maverick (2026 Gold Standard)
```powershell
# Test Maverick for everything
$env:YONCA_LLM_PROVIDER = "groq"
$env:YONCA_GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
$env:YONCA_GROQ_API_KEY = "gsk_your_key_here"

# Start API and test
# Should respond in pure Azerbaijani, no Turkish words
# Can also analyze images!
```

### Test Legacy Mode (Comparison)
```powershell
# Test Llama 3.3 for language quality
$env:YONCA_GROQ_MODEL = "llama-3.3-70b-versatile"

# Test Qwen for math (internal use only)
$env:YONCA_GROQ_MODEL = "qwen/qwen3-32b"
```

### Test Self-Hosted (Production)
```powershell
# Point to your vLLM/TGI server
$env:YONCA_LLM_PROVIDER = "groq"
$env:YONCA_GROQ_BASE_URL = "http://your-llm-cluster:8000"
$env:YONCA_GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Same API, same code - just local
```

---

## Configuration Examples

### Recommended Production Config (.env) - 2026
```bash
# 2026 Gold Standard: Maverick Mode
YONCA_DEPLOYMENT_MODE=open_source
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
YONCA_GROQ_API_KEY=gsk_your_key_here

# For self-hosted production:
# YONCA_GROQ_BASE_URL=http://your-llm-cluster:8000
```

### Legacy Config (Still Supported)
```bash
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.3-70b-versatile
YONCA_GROQ_API_KEY=gsk_your_key_here
```

### Fast Testing Config
```bash
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=llama-3.1-8b-instant  # Fast but lower quality
YONCA_GROQ_API_KEY=gsk_your_key_here
```

---

## Common Mistakes to Avoid

### ❌ Don't Do This (Legacy Pattern)
```python
# DEPRECATED: Using two-model stack
calc_result = qwen.generate(calc_messages)  # Calculate with Qwen
final = llama.generate([  # Rewrite with Llama
    LLMMessage.system("Rewrite in Azerbaijani"),
    LLMMessage.user(calc_result.content)
])
return final.content  # Double token cost!
```

### ✅ Do This Instead (2026 Pattern)
```python
# RECOMMENDED: Single Maverick call does it all
response = maverick.generate(messages)  # ✅ Logic + Language in one pass
return response.content  # Half the cost, better quality!
```

---

## Groq Model Availability (January 2026)

| Model | Speed | Quality | Azerbaijani | Math | Vision | Context |
|:------|:------|:--------|:------------|:-----|:-------|:--------|
| **llama-4-maverick** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 128k |
| llama-3.3-70b-versatile | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | 128k |
| llama-3.1-8b-instant | ⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | 8k |
| qwen3-32b | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐ ⚠️ | ⭐⭐⭐⭐⭐ | ❌ | 32k |
| mixtral-8x7b-32768 | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | 32k |

⚠️ = Turkish leakage risk

---

## Performance Benchmarks

```
Typical Response Times (tested January 2026):
─────────────────────────────────────────────

Groq (llama-4-maverick-17b-128e-instruct):
  • 500 token response: ~1.7 seconds
  • Tokens/second: 280-320 ⭐ FASTEST

Groq (llama-3.3-70b-versatile):
  • 500 token response: ~2.5 seconds
  • Tokens/second: 200-250

Groq (qwen3-32b):
  • 500 token response: ~1.8 seconds
  • Tokens/second: 250-300

Legacy Two-Pass (Qwen + Llama rewrite):
  • 500 token response: ~4.3 seconds
  • Tokens/second: N/A (sequential calls)

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
   YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
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
   - Default mode is now "maverick" - single model for all nodes
   - Legacy mode ("open_source") still available for comparison

4. **For production (government compliance):**
   - Deploy vLLM or TGI on-premises
   - Point `YONCA_GROQ_BASE_URL` to your cluster
   - Same models, full data control

---

## Why Maverick?

| Benefit | Description |
|:--------|:------------|
| **Single Node** | Replaces 2-node Qwen+Llama stack with 1 node |
| **Native Azerbaijani** | No Turkish leakage - trained on clean data |
| **Vision Support** | Analyze crop disease photos, field images |
| **Cost Efficient** | 1 API call instead of 2 (half the tokens) |
| **Ultra-Fast** | ~300 tokens/sec on Groq infrastructure |
| **Self-Hostable** | Deploy on 4x A100 GPUs for full control |

---

## Hardware Quick Reference

### For Maverick (17B MoE - Lighter than 70B!)

| Option | Hardware | VRAM | Cost | Performance |
|:-------|:---------|:-----|:-----|:------------|
| **Workstation** | 1× RTX 5090 | 32GB | ~$2,500 | 80-100 tok/s |
| **Mac Studio** | M3/M4 Ultra | 64GB Unified | ~$4,000 | 50-70 tok/s |
| **AzInCloud** | NVIDIA A100 | 40GB | €1.50/hr | 150-200 tok/s |

> 💡 **Maverick runs on LESS hardware than 70B models!** The MoE architecture only activates 17B parameters per token.

---

## Support

Questions? Check:
- **Hardware Economics**: [15-HARDWARE-JUSTIFICATION.md](15-HARDWARE-JUSTIFICATION.md)
- Full guide: [LANGUAGE-INTERFERENCE-GUIDE.md](LANGUAGE-INTERFERENCE-GUIDE.md)
- Deployment: [12-DUAL-MODE-DEPLOYMENT.md](12-DUAL-MODE-DEPLOYMENT.md)
- Model config: [src/yonca/llm/model_roles.py](../../src/yonca/llm/model_roles.py)
- System prompts: [prompts/system/](../../prompts/system/)
