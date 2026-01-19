# 🎯 ALEM 1.0 — Deployment Decision Guide

> **ALEM** = **A**gronomical **L**ogic & **E**valuation **M**odel

## One-Minute Overview

**All models are 100% open-source** (Llama, Qwen, Mixtral)

| What | Where | Cost | Speed | Data |
|------|-------|------|-------|------|
| **DigiRella Owned** | Self-hosted (AZ) | $2,600-145k one-time | 300 tok/s 🏠 | Azerbaijan ✅ |
| **DigiRella Cloud** | AzInTelecom (AZ) | $800-1,500/mo | 300 tok/s ☁️ | Azerbaijan ✅ |
| *Benchmark Demo* | *Cloud API (for dev)* | *$0-50/mo* | *300 tok/s ⚡* | *External (dev only)* |

## The ALEM 1.0 Philosophy

> **We demonstrate performance via cloud APIs** (to show what's possible)  
> **You deploy via DigiRella** (Owned hardware or AzInTelecom Cloud)  
> **Result: Enterprise AI with 100% data sovereignty**

## ALEM 1.0 Deployment Options

### Development Phase: Cloud API Benchmark
- **Cost:** Free tier (14,400 req/day)
- **Setup:** Just API key (for testing)
- **Use for:** Validating architecture, demos
- **Limitation:** Data goes to external servers (development only)

### Production Mode 1: DigiRella Cloud (Rented)
- **Cost:** $800-1,500/mo (rented GPU from AzInTelecom)
- **Setup:** 1-2 weeks (contract)
- **Use for:** Government, regulated industries, scalable production
- **Benefit:** Data stays in Azerbaijan 🇦🇿, same performance as benchmark

### Production Mode 2: DigiRella Owned (Self-Hosted)
- **Cost:** $2,600 (Lite) to $145k (Pro) one-time
- **Setup:** 2-6 weeks (hardware procurement)
- **Use for:** Long-term deployment, air-gapped
- **Benefit:** No recurring costs, complete control

## Hardware Quick Guide

**DigiRella Lite** ($2,600)
- 1× RTX 4090
- 300+ tok/s
- Llama 3.1 8B

**DigiRella Standard** ($6,300) ⭐ Recommended
- 2× RTX 5090
- 200+ tok/s
- Llama 3.3 70B (same as Groq)

**DigiRella Pro** ($145,000)
- 8× A100
- 300+ tok/s
- ALL models (Groq-equivalent)

## ALEM 1.0 Adoption Path

```
Phase 1 (Dev):    Cloud Benchmark API   → Validate architecture ($0)
Phase 2 (Pilot):  DigiRella Cloud       → Production pilot ($1,500/mo)
Phase 3 (Scale):  DigiRella Owned       → Long-term ownership ($6,300 one-time)
```

> 💡 All phases use the same open-source models (Llama, Qwen). Only infrastructure changes.

## Break-Even Analysis

**DigiRella Standard ($6,300) vs DigiRella Cloud ($1,500/mo)**

- Month 4: Break-even ✅
- Year 2: Save $29,700
- Year 5: Save $83,700

## 🔗 Full Documentation

- **Pricing:** [docs/PRICING-SIMPLIFIED.md](../PRICING-SIMPLIFIED.md)
- **Hardware:** [docs/zekalab/17-DIGIRELLA-HOSTING-PROFILES.md](../zekalab/17-DIGIRELLA-HOSTING-PROFILES.md)
- **Tiers:** [docs/zekalab/16-ALEM-INFRASTRUCTURE-TIERS.md](../zekalab/16-ALEM-INFRASTRUCTURE-TIERS.md)

---

*Last updated: January 19, 2026*
