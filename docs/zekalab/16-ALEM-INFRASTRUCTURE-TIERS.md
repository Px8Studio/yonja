# ALEM Infrastructure Matrix

> **ALEM** = Azərbaycan LLM Ekosistem Matrisi

This document defines the four-tier infrastructure model for LLM deployment in Azerbaijan, from rapid prototyping to air-gapped sovereign installations.

---

## 🏗️ Tier Overview

| Tier | Name | Provider | Latency | Data Residency | Cost Range |
|------|------|----------|---------|----------------|------------|
| **I** | Groq LPU | Groq Cloud | ~200ms | US (Groq servers) | $0–50/mo |
| **II** | Google Gemini | Google Cloud | ~400ms | EU (Vertex AI) | $20–300/mo |
| **III** | AzInTelecom | Sovereign Cloud | ~600ms | Azerbaijan 🇦🇿 | $800–1,500/mo |
| **IV** | ZekaLab Custom | On-Prem | ~300ms | Customer premises | $6,500–12,000 one-time |

---

## ⚡ Tier I: Groq LPU — Rapid Prototyping

**Best for:** Hackathons, demos, MVPs, development/testing

| Specification | Value |
|--------------|-------|
| **Provider** | Groq Cloud |
| **Models** | Llama 4 Maverick 17B, Qwen 3 32B |
| **Latency** | ~200ms (P95) |
| **Throughput** | 800 tok/s |
| **Data Residency** | US (Groq servers) |
| **Cost** | Free tier available, $0–50/mo for dev workloads |

### Configuration

```env
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_API_KEY=gsk_...
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
```

### Pros
- ✅ Fastest inference (LPU hardware)
- ✅ Free tier for experimentation
- ✅ Open-source models (Llama, Qwen, Mistral)
- ✅ Zero infrastructure management

### Cons
- ⚠️ Data leaves Azerbaijan
- ⚠️ Rate limits on free tier
- ⚠️ External dependency

---

## 🧠 Tier II: Google Gemini — High Reasoning

**Best for:** Complex reasoning, multimodal, production pilots

| Specification | Value |
|--------------|-------|
| **Provider** | Google Cloud (Vertex AI) |
| **Models** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **Latency** | ~400ms (P95) |
| **Throughput** | 150 tok/s |
| **Data Residency** | EU (via Vertex AI region lock) |
| **Cost** | $20–300/mo |

### Configuration

```env
YONCA_LLM_PROVIDER=gemini
YONCA_GEMINI_API_KEY=AI...
YONCA_GEMINI_MODEL=gemini-2.0-flash-exp
```

### Pros
- ✅ Best-in-class reasoning
- ✅ Multimodal (vision, audio)
- ✅ EU data residency option
- ✅ Enterprise SLAs available

### Cons
- ⚠️ Proprietary (closed-source)
- ⚠️ Higher cost
- ⚠️ Data leaves Azerbaijan

---

## 🏛️ Tier III: AzInTelecom — Sovereign Cloud

**Best for:** Government, regulated industries, data sovereignty requirements

| Specification | Value |
|--------------|-------|
| **Provider** | AzInTelecom Government Cloud |
| **Models** | Llama 3.3 70B, Mistral Large |
| **Latency** | ~600ms (P95) |
| **Throughput** | 80 tok/s |
| **Data Residency** | Azerbaijan 🇦🇿 (Baku DC) |
| **Cost** | $800–1,500/mo |

### Configuration

```env
YONCA_LLM_PROVIDER=azintelecom
YONCA_AZINTELECOM_BASE_URL=https://llm.gov.az/v1
YONCA_AZINTELECOM_API_KEY=...
YONCA_AZINTELECOM_MODEL=llama-3.3-70b
```

### Pros
- ✅ **100% data sovereignty** — data never leaves Azerbaijan
- ✅ Government-grade security
- ✅ Compliance with local regulations
- ✅ SLA guarantees

### Cons
- ⚠️ Higher latency than cloud providers
- ⚠️ Limited model selection
- ⚠️ Higher cost

### Use Cases
- Government agricultural portals
- Ministry of Agriculture integrations
- Financial institutions (AzeriCard, banks)
- Healthcare data processing

---

## 🔒 Tier IV: ZekaLab Custom — Private On-Prem

**Best for:** Offline farms, military, banks, air-gapped networks

| Specification | Value |
|--------------|-------|
| **Provider** | Self-hosted (customer premises) |
| **Models** | ATLLaMA 7B, Qwen 3 4B, custom fine-tunes |
| **Latency** | ~300ms (P95) |
| **Throughput** | 40 tok/s (CPU) / 200 tok/s (GPU) |
| **Data Residency** | Customer premises (air-gapped option) |
| **Cost** | $6,500–12,000 one-time hardware |

### Configuration (Ollama)

```env
YONCA_LLM_PROVIDER=ollama
YONCA_OLLAMA_BASE_URL=http://localhost:11434
YONCA_OLLAMA_MODEL=atllama:7b
```

### Hardware Requirements

**Minimum (CPU-only):**
- Intel i7/Xeon or AMD Ryzen 7
- 32GB RAM
- 256GB SSD
- ~$2,000

**Recommended (GPU):**
- NVIDIA RTX 4090 or A6000
- 64GB RAM
- 1TB NVMe SSD
- ~$8,000

**Enterprise (Multi-GPU):**
- 2× NVIDIA A100 80GB
- 256GB RAM
- 2TB NVMe RAID
- ~$25,000

### Pros
- ✅ **Complete data isolation** — air-gap capable
- ✅ No internet dependency
- ✅ One-time cost (no recurring fees)
- ✅ Custom fine-tuning possible

### Cons
- ⚠️ Requires hardware investment
- ⚠️ Maintenance responsibility
- ⚠️ Smaller models (7B–13B typical)

### Use Cases
- Remote farms with poor connectivity
- Military/defense applications
- Banking secure zones
- GDPR/KVKK extreme compliance

---

## 📊 Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ALEM Decision Tree                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Is data sovereignty MANDATORY?                                     │
│  ├── YES → Is air-gap required?                                     │
│  │         ├── YES → Tier IV (On-Prem)                             │
│  │         └── NO  → Tier III (AzInTelecom)                        │
│  │                                                                  │
│  └── NO  → Is complex reasoning needed?                            │
│            ├── YES → Is budget > $100/mo?                          │
│            │         ├── YES → Tier II (Gemini)                    │
│            │         └── NO  → Tier I (Groq)                       │
│            │                                                        │
│            └── NO  → Tier I (Groq) — fastest & cheapest            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Runtime Tier Detection

The system automatically detects the current tier based on `YONCA_LLM_PROVIDER`:

```python
from yonca.config import settings

# Get current tier
print(settings.inference_tier)  # e.g., InferenceTier.TIER_I_GROQ

# Get full specification
spec = settings.inference_tier_spec
print(f"Provider: {spec['provider']}")
print(f"Latency: {spec['latency']}")
print(f"Data Residency: {spec['data_residency']}")
```

### Banner Display

The startup banner automatically shows the current tier:

```
  ─────────────────────────────────────────────────────────
  🏗️  ALEM Infrastructure Tier
  ─────────────────────────────────────────────────────────

  ⚡  Tier I: Groq LPU
     Rapid Prototyping

     Provider: Groq Cloud
     Latency: ~200ms (P95)
     Throughput: 800 tok/s
     Data Residency: US (Groq servers)
     Cost Range: $0–50/mo (dev)

     Models: Llama 4 Maverick 17B, Qwen 3 32B
     Best for: Hackathons, demos, MVPs, dev/test
```

---

## 🚀 Migration Path

1. **Development:** Start with Tier I (Groq) — fast iteration, free tier
2. **Pilot:** Validate with real users on Tier I or II
3. **Production:** Choose based on data residency requirements:
   - International: Tier II (Gemini) with EU residency
   - Azerbaijan-only: Tier III (AzInTelecom)
   - Air-gapped: Tier IV (On-Prem)

---

## 📎 Related Documentation

- [03-ARCHITECTURE.md](./03-ARCHITECTURE.md) — System architecture
- [12-DUAL-MODE-DEPLOYMENT.md](./12-DUAL-MODE-DEPLOYMENT.md) — Deployment modes
- [15-HARDWARE-JUSTIFICATION.md](./15-HARDWARE-JUSTIFICATION.md) — Hardware requirements

---

*Last updated: 2025 | ZekaLab Yonca AI Project*
