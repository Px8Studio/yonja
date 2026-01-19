# 💰 Yonca AI Pricing & Deployment Options (Simplified)

**Last updated:** January 19, 2026

---

## 🎯 TL;DR — Three Simple Options

| Option | Cost | Performance | Data Location | Best For |
|--------|------|-------------|---------------|----------|
| **Groq Cloud** | $0-50/mo | 200-300 tok/s | 🇺🇸 US | Development, testing, demos |
| **DigiRella Cloud** | $800-1,500/mo | 200-300 tok/s | 🇦🇿 Azerbaijan | Government, production (rented) |
| **DigiRella Owned** | $2,600-145k one-time | 200-300 tok/s | 🏠 Your premises | Long-term, air-gapped, full ownership |

---

## 📊 Detailed Comparison

### Option 1: Groq Cloud (Benchmark)

**What is it?** Cloud API using Groq's LPU (Language Processing Unit) infrastructure.

**Performance:**
- Llama 4 Maverick 17B: 300 tok/s
- Llama 3.3 70B: 200+ tok/s
- Qwen 3 32B: 280 tok/s
- Latency: ~200ms (P95)

**Cost:**
- Free tier: 14,400 requests/day
- Paid: ~$0.10 per 1M tokens
- Typical usage: $10-50/mo for development

**Pros:**
- ✅ Fastest to start (just API key)
- ✅ Zero infrastructure management
- ✅ Free tier for experimentation
- ✅ 100% open-source models

**Cons:**
- ❌ Data leaves Azerbaijan (US servers)
- ❌ Rate limits on free tier
- ❌ Internet dependency

**When to use:** Development, testing, POC, demos

---

### Option 2: DigiRella Cloud (Rented GPU)

**What is it?** Rented GPU capacity from AzInTelecom (Baku data centers). Same models as Groq, but data stays in Azerbaijan.

**Performance:**
- Current: 80 tok/s (optimizing)
- Target: 200-300 tok/s (Groq-equivalent)
- Latency: ~600ms → target: ~250ms

**Cost:**
- Lite (8B models): ~$470/mo
- Standard (70B models): ~$1,900/mo
- Enterprise (multi-instance): ~$7,600/mo

**Pros:**
- ✅ **Data sovereignty** (100% Azerbaijan 🇦🇿)
- ✅ No hardware purchase needed
- ✅ Same open-source models as Groq
- ✅ Government-approved infrastructure
- ✅ SLA guarantees

**Cons:**
- ❌ Recurring monthly cost
- ❌ Requires contract with AzInTelecom
- ❌ Performance optimization in progress

**When to use:** Government projects, regulated industries, production deployment with data sovereignty

---

### Option 3: DigiRella Owned (Self-Hosted)

**What is it?** Hardware you own and operate. Achieves same performance as Groq with appropriate GPU configuration.

**Three profiles to choose from:**

#### DigiRella Lite ($2,600)
- **Hardware:** 1× NVIDIA RTX 4090 (24GB)
- **Performance:** 300+ tok/s
- **Models:** Llama 3.1 8B, Qwen 3 4B
- **Best for:** Single-farm pilot, testing

#### DigiRella Standard ($6,300)
- **Hardware:** 2× NVIDIA RTX 5090 (64GB total)
- **Performance:** 200+ tok/s
- **Models:** Llama 3.3 70B, Qwen 3 32B, Maverick 17B
- **Best for:** Regional cooperative (5,000-10,000 farmers)

#### DigiRella Pro ($145,000)
- **Hardware:** 8× NVIDIA A100 80GB
- **Performance:** 300+ tok/s (full Groq-equivalent)
- **Models:** ALL models simultaneously
- **Best for:** National deployment (100,000+ farmers)

**Cost Breakdown (Standard Profile):**
- Hardware: $6,300 (one-time)
- Electricity: ~$150/year
- **2-Year TCO:** $6,600
- **Break-even vs Cloud:** 3-4 months

**Pros:**
- ✅ **Complete data isolation** (air-gapped capable)
- ✅ **No recurring costs** (only electricity)
- ✅ **Full ownership** (customize, fine-tune)
- ✅ Groq-equivalent performance
- ✅ Works offline (no internet required)

**Cons:**
- ❌ Upfront investment required
- ❌ Hardware maintenance responsibility
- ❌ Requires technical expertise

**When to use:** Long-term deployment, remote farms, military/defense, banking, complete data control

---

## 🚀 Migration Path (Recommended)

```
Phase 1: Development (0-3 months)
├─ Use: Groq Cloud (Free Tier)
├─ Cost: $0
└─ Purpose: Validate idea, build MVP

Phase 2: Pilot (3-12 months)
├─ Use: DigiRella Cloud (Rented) OR DigiRella Standard (Owned)
├─ Cost: $1,900/mo (rented) OR $6,300 one-time (owned)
└─ Purpose: 100-5,000 farmers, real-world testing

Phase 3: Production (12+ months)
├─ Use: DigiRella Owned (Standard or Pro)
├─ Cost: $6,300-145,000 (one-time)
└─ Purpose: National scale, lowest TCO
```

---

## 💵 Total Cost of Ownership (2-Year Comparison)

| Scenario | 5,000 Farmers | 50,000 Farmers | 100,000 Farmers |
|----------|---------------|----------------|-----------------|
| **Groq Paid** | $1,200 | $12,000 | $24,000 |
| **DigiRella Cloud** | $11,280 | $45,600 | $91,200 |
| **DigiRella Standard (Owned)** | **$6,600** ✅ | **$6,600** ✅ | N/A (need Pro) |
| **DigiRella Pro (Owned)** | N/A | $145,300 | **$145,300** ✅ |

**Key insight:** Owned hardware pays for itself in 6-12 months for production workloads.

---

## 🛠️ How to Get Started

### Groq Cloud (Immediate)

1. Sign up: [console.groq.com](https://console.groq.com)
2. Get API key
3. Set in `.env`:
   ```env
   YONCA_LLM_PROVIDER=groq
   YONCA_GROQ_API_KEY=gsk_...
   ```
4. Run Yonca AI: `docker-compose up`

### DigiRella Cloud (1-2 weeks)

1. Contact AzInTelecom: enterprise@azintelecom.az
2. Sign service contract
3. Receive API credentials
4. Configure `.env`:
   ```env
   YONCA_LLM_PROVIDER=azintelecom
   YONCA_AZINTELECOM_API_KEY=...
   ```

### DigiRella Owned (2-6 weeks)

1. Procure hardware (see [17-DIGIRELLA-HOSTING-PROFILES.md](../zekalab/17-DIGIRELLA-HOSTING-PROFILES.md))
2. Install Ubuntu 22.04 + CUDA drivers
3. Deploy Yonca AI stack:
   ```bash
   git clone https://github.com/Px8Studio/yonja.git
   cd yonja
   ./scripts/setup_DigiRella.sh --profile standard
   ```

---

## ❓ Frequently Asked Questions

**Q: Why is it called "DigiRella"?**  
A: Digital + Relay + Azerbaijan = "Digital Farm Relay". Brand for self-hosted LLM infrastructure.

**Q: Are all models open-source?**  
A: Yes! Llama, Qwen, Mistral, Mixtral are all 100% open-source. No proprietary models.

**Q: Can I start with Groq and switch later?**  
A: Absolutely! Same models, same API. Just change environment variables.

**Q: What's the difference between Groq and DigiRella?**  
A: Groq proves the benchmark (what's possible). DigiRella lets you replicate that performance with your own/rented hardware.

**Q: Do I need to choose one option forever?**  
A: No! You can mix modes:
- Groq for development
- DigiRella Cloud for burst capacity
- DigiRella Owned for steady-state production

**Q: What about electricity costs?**  
A: DigiRella Standard: ~$150/year (~12 kWh/day @ $0.05/kWh in Baku)

**Q: Can I fine-tune models?**  
A: Only with DigiRella Owned. Not possible with Groq or DigiRella Cloud.

**Q: What about data privacy?**  
A: 
- Groq: Data goes to US servers
- DigiRella Cloud: Data stays in Azerbaijan
- DigiRella Owned: Data never leaves your premises

**Q: What if I outgrow hardware?**  
A: Upgrade GPU configuration or add more nodes. Horizontal scaling supported.

---

## 📎 Related Documentation

- [17-DIGIRELLA-HOSTING-PROFILES.md](../zekalab/17-DIGIRELLA-HOSTING-PROFILES.md) — Full hardware specs
- [16-ALEM-INFRASTRUCTURE-TIERS.md](../zekalab/16-ALEM-INFRASTRUCTURE-TIERS.md) — Tier comparison
- [15-HARDWARE-JUSTIFICATION.md](../zekalab/15-HARDWARE-JUSTIFICATION.md) — Economic analysis

---

## 📞 Need Help Choosing?

Contact ZekaLab for consultation:
- Email: team@zekalab.io
- Telegram: @zekalab
- GitHub Discussions: [yonja/discussions](https://github.com/Px8Studio/yonja/discussions)

---

*Document Version: 1.0 | Created: January 19, 2026*
