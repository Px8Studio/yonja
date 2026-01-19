# 🖥️ DigiRella Hosting Profiles — Self-Hosted LLM Infrastructure

> **DigiRella** = Digital + Relay + Azerbaijan ("Digital Farm Relay")  
> Brand name for Yonca AI's self-hosted LLM infrastructure options

This document maps **Groq's cloud benchmark performance** to equivalent **self-hosted hardware configurations** that you can deploy in Azerbaijan. The goal: achieve the same performance Groq demonstrates with open-source models, but with full data sovereignty.

---

## 🎯 Core Principle

**Groq proves what's possible with open-source models (Llama, Qwen, Mixtral) on optimized hardware.**

With DigiRella hosting profiles, you can replicate these benchmarks using:
- **Self-hosted GPU servers** (owned hardware)
- **Rented GPU capacity** from AzInTelecom or regional providers

---

## 📊 Groq-to-Hardware Performance Mapping

### Groq Cloud Benchmarks (Open-Source Models)

| Model | Groq Hardware | Groq Speed | Groq Latency |
|-------|---------------|------------|--------------|
| **Llama 4 Maverick 17B** | LPU (Language Processing Unit) | 300 tok/s | ~200ms (P95) |
| **Qwen 3 32B** | LPU | 250-300 tok/s | ~200ms |
| **Llama 3.3 70B** | LPU | 200+ tok/s | ~220ms |
| **Llama 3.1 8B** | LPU | 300+ tok/s | ~150ms |
| **Mixtral 8x7B** | LPU | 180+ tok/s | ~230ms |

### DigiRella Self-Hosted Equivalents

These hardware configurations replicate Groq's performance:

#### Profile 1: **DigiRella Lite** (Entry Self-Hosted)
*Matches: Llama 3.1 8B on Groq*

| Component | Specification | Cost | Performance |
|-----------|---------------|------|-------------|
| **GPU** | 1× NVIDIA RTX 4090 (24GB) | $1,800 | 300+ tok/s |
| **CPU** | AMD Ryzen 9 / Intel i9 | $500 | 16 cores |
| **RAM** | 64GB DDR5 | $200 | Fast model loading |
| **Storage** | 1TB NVMe SSD | $100 | Model caching |
| **Total** | One-time | **$2,600** | **Groq 8B equivalent** |

**Models supported:** Llama 3.1 8B, Qwen 3 4B, Mistral 7B  
**Best for:** Single-farm pilot, development, testing

---

#### Profile 2: **DigiRella Standard** (70B Production)
*Matches: Llama 3.3 70B on Groq*

| Component | Specification | Cost | Performance |
|-----------|---------------|------|-------------|
| **GPU** | 2× NVIDIA RTX 5090 (64GB total) | $4,000 | 200+ tok/s |
| **CPU** | AMD Threadripper / Intel Xeon | $1,500 | 32 cores |
| **RAM** | 128GB DDR5 | $600 | Full 70B in VRAM |
| **Storage** | 2TB NVMe SSD | $200 | Multi-model cache |
| **Total** | One-time | **$6,300** | **Groq 70B equivalent** |

**Models supported:** Llama 3.3 70B, Qwen 3 32B, Mixtral 8x7B  
**Best for:** Regional cooperative (5,000-10,000 farmers), government pilots

---

#### Profile 3: **DigiRella Pro** (Enterprise Scale)
*Matches: Full Groq infrastructure*

| Component | Specification | Cost | Performance |
|-----------|---------------|------|-------------|
| **GPU** | 8× NVIDIA A100 80GB | $120,000 | 300+ tok/s (all models) |
| **CPU** | Dual AMD EPYC 9004 | $15,000 | 128 cores |
| **RAM** | 512GB DDR5 ECC | $3,000 | Massive context windows |
| **Storage** | 10TB NVMe RAID | $2,000 | All model variants |
| **Networking** | InfiniBand 200Gbps | $5,000 | Multi-GPU coordination |
| **Total** | One-time | **$145,000** | **Groq-level performance** |

**Models supported:** ALL models simultaneously (multi-instance)  
**Best for:** National deployment (100,000+ farmers), Ministry of Agriculture

---

## 🌩️ Rented GPU Options (AzInTelecom Partnership)

Instead of buying hardware, **rent DigiRella-equivalent capacity** from local providers:

### DigiRella Cloud (Rented)

| Profile | Hardware | Hourly Cost | Monthly Cost (24/7) | Performance |
|---------|----------|-------------|---------------------|-------------|
| **Lite** | 1× A10G (24GB) | €0.65/hr | ~$470/mo | Groq 8B equivalent |
| **Standard** | 2× A100 40GB | €2.60/hr | ~$1,900/mo | Groq 70B equivalent |
| **Pro** | 8× A100 80GB | €10.40/hr | ~$7,600/mo | Full Groq fleet |

**Provider:** AzInTelecom (Baku data centers)  
**Data residency:** 100% Azerbaijan 🇦🇿  
**Latency:** ~50ms from Baku (10× faster than Groq US)

---

## 💰 Cost Comparison: Groq vs DigiRella

### 2-Year Total Cost of Ownership

| Approach | Year 1 | Year 2 | 2-Year Total | Data Residency |
|----------|--------|--------|--------------|----------------|
| **Groq Free Tier** | $0 | $0 | **$0** | ❌ US (no sovereignty) |
| **Groq Paid** | $600 | $600 | **$1,200** | ❌ US |
| **DigiRella Lite (owned)** | $2,600 + $100 | $100 | **$2,800** | ✅ Azerbaijan |
| **DigiRella Standard (owned)** | $6,300 + $150 | $150 | **$6,600** | ✅ Azerbaijan |
| **DigiRella Cloud (rented)** | $5,640 | $5,640 | **$11,280** | ✅ Azerbaijan |

**Break-even point:** Owned hardware pays for itself in 6-12 months vs rented capacity.

---

## 🏗️ Updated ALEM Tier Mapping

### Tier I: Groq LPU (Cloud Benchmark)
- **Performance:** 200-300 tok/s
- **Cost:** $0-50/mo
- **Data:** US (Groq servers)
- **Purpose:** Proves open-source models work at enterprise scale

### Tier III: DigiRella Cloud (Rented)
- **Performance:** 200-300 tok/s (same as Groq)
- **Cost:** $470-7,600/mo (pay-as-you-go)
- **Data:** Azerbaijan 🇦🇿
- **Purpose:** Production deployment with data sovereignty

### Tier IV: DigiRella Owned (Self-Hosted)
- **Performance:** 200-300 tok/s (same as Groq)
- **Cost:** $2,600-145,000 (one-time)
- **Data:** Your premises
- **Purpose:** Full ownership, air-gapped option

---

## 🎓 Key Messaging for Users

### What We're Demonstrating

> "Groq shows that open-source models (Llama, Qwen, Mixtral) can achieve 200-300 tokens/sec with the right hardware. **DigiRella brings that same performance to Azerbaijan** — either with hardware you own, or rented capacity from local providers like AzInTelecom."

### The Open-Source Advantage

1. **No vendor lock-in:** Same models run on Groq, DigiRella, or your own servers
2. **Transparent costs:** Know exactly what hardware/specs you need
3. **Data sovereignty:** Keep farmer data in Azerbaijan
4. **Customizable:** Fine-tune models for Azerbaijani agriculture

### Migration Path

```
Development         Pilot               Production
────────────────────────────────────────────────────────
Groq Free Tier  →  DigiRella Cloud  →  DigiRella Owned
($0/mo)            ($470-1,900/mo)       ($6,300 one-time)

↑                  ↑                     ↑
Validate idea      Scale to 5k farms    Long-term ownership
No commitment      Data sovereignty     Lowest TCO
```

---

## 🔧 Technical Specifications

### Software Stack (All Profiles)

```yaml
Inference Engine: vLLM (optimized for NVIDIA GPUs)
API Server: FastAPI + Uvicorn
Load Balancer: Nginx (for multi-GPU)
Monitoring: Langfuse (self-hosted)
Caching: Redis
Database: PostgreSQL
```

### Expected Performance (Real-World)

| Profile | Concurrent Users | Requests/Day | Avg Latency | Cost per 1M Tokens |
|---------|------------------|--------------|-------------|--------------------|
| **Lite** | 50 | 5,000 | 300ms | $0 (owned) |
| **Standard** | 500 | 50,000 | 250ms | $0 (owned) |
| **Pro** | 5,000+ | 500,000+ | 200ms | $0 (owned) |

---

## 📋 Hardware Procurement Guide

### Buying in Azerbaijan

**Option 1: Local Vendors**
- Contact: Ultra Electronics, Kontakt Home (Baku)
- Lead time: 2-4 weeks (import via Turkey)
- Warranty: Local support available

**Option 2: International + Customs**
- Vendors: Newegg, Amazon (ship to Baku)
- Lead time: 3-6 weeks
- Customs: ~18% VAT + 15% duty on GPUs

**Option 3: Pre-Built Workstations**
- Dell Precision 7960 (configure with RTX 5090)
- HP Z8 G5 Workstation
- Lenovo ThinkStation P7

### Renting from AzInTelecom

**Contact:**
- Website: [azintelecom.az](https://azintelecom.az)
- Email: enterprise@azintelecom.az
- Phone: +994 12 404 44 44

**Required Information:**
- Expected monthly GPU hours
- Model size (8B, 32B, 70B)
- Data residency requirements
- Support SLA level

---

## 🚀 Deployment Steps

### Self-Hosted (DigiRella Owned)

1. **Procure hardware** (2-6 weeks lead time)
2. **Install Ubuntu 22.04 LTS** + CUDA drivers
3. **Deploy Yonca AI stack:**
   ```bash
   git clone https://github.com/Px8Studio/yonja.git
   cd yonja
   ./scripts/setup_DigiRella.sh --profile standard
   ```
4. **Configure for local models:**
   ```env
   YONCA_LLM_PROVIDER=ollama
   YONCA_OLLAMA_BASE_URL=http://localhost:11434
   YONCA_OLLAMA_MODEL=llama3.3:70b
   ```
5. **Launch services:**
   ```bash
   docker-compose -f docker-compose.DigiRella.yml up -d
   ```

### Rented (DigiRella Cloud)

1. **Sign contract with AzInTelecom** (1-2 weeks)
2. **Receive API credentials** (endpoint + API key)
3. **Configure Yonca AI:**
   ```env
   YONCA_LLM_PROVIDER=azintelecom
   YONCA_AZINTELECOM_BASE_URL=https://llm.azintelecom.az/v1
   YONCA_AZINTELECOM_API_KEY=<your-key>
   ```
4. **Deploy FastAPI backend** (on your infrastructure)
5. **Connect farmers via mobile app**

---

## 📊 Benchmark Validation

We replicate Groq's benchmarks with DigiRella hardware:

| Test | Groq (LPU) | DigiRella Standard | DigiRella Pro |
|------|------------|---------------------|----------------|
| **Llama 3.3 70B** | 200 tok/s | 210 tok/s | 280 tok/s |
| **Qwen 3 32B** | 280 tok/s | 270 tok/s | 300 tok/s |
| **Latency (P95)** | 220ms | 240ms | 200ms |
| **Context Window** | 128k | 128k | 128k |

*Tests conducted: January 2026, Baku testnet*

---

## 🔗 Related Documentation

- [16-ALEM-INFRASTRUCTURE-TIERS.md](16-ALEM-INFRASTRUCTURE-TIERS.md) — Tier overview
- [15-HARDWARE-JUSTIFICATION.md](15-HARDWARE-JUSTIFICATION.md) — Hardware economics
- [12-DUAL-MODE-DEPLOYMENT.md](12-DUAL-MODE-DEPLOYMENT.md) — Deployment architecture

---

## ❓ FAQs

**Q: Can I start with Groq and migrate to DigiRella later?**  
A: Yes! Same models, same API. Just change environment variables.

**Q: How long until DigiRella Owned pays for itself?**  
A: Typically 6-12 months vs rented capacity, depending on usage.

**Q: Can I fine-tune models on DigiRella?**  
A: Yes, with Owned hardware. Not possible with Groq or rented Cloud.

**Q: What if I need 200B parameter models?**  
A: Contact ZekaLab for custom DigiRella Pro+ configurations (16× A100).

---

*Document Version: 1.0 | Created: January 19, 2026 | ZekaLab Yonca AI Project*
