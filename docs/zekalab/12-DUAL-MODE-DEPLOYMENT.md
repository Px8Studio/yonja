# 🔀 Yonca AI — Dual-Mode Deployment Architecture

> **Purpose:** Define the dual-mode deployment strategy supporting both **Open-Source** (Groq or self-hosted LLMs) and **Proprietary Cloud** (Gemini API) deployments.

---

## ✅ Implementation Status (January 2026)

```mermaid
%%{init: {'theme': 'neutral'}}%%
pie showData
    title Provider Implementation
    "✅ Groq (Production)" : 40
    "✅ Ollama (Local Dev)" : 35
    "✅ Gemini (Fallback)" : 25
```

### Provider Comparison

```mermaid
%%{init: {'theme': 'neutral'}}%%
quadrantChart
    title LLM Providers: Speed vs Self-Hosting
    x-axis Low Speed --> High Speed
    y-axis No Self-Host --> Full Self-Host
    quadrant-1 Best: Fast + Self-Hostable
    quadrant-2 Good: Self-Hostable
    quadrant-3 Risky: Slow + Locked
    quadrant-4 Convenient: Fast but Locked
    Groq: [0.85, 0.75]
    Ollama: [0.35, 0.95]
    Gemini: [0.70, 0.15]
    vLLM: [0.65, 0.90]
```

---

## 🎯 Open-Source First Philosophy

Yonca AI is built on **open-source models** to demonstrate enterprise-ready AI that:

✅ **Can be self-hosted** - Full control over deployment  
✅ **No vendor lock-in** - Not dependent on proprietary APIs  
✅ **Transparent & auditable** - Open weights, open architectures  
✅ **Production-ready** - Enterprise performance with proper infrastructure (200-300 tok/s)

---

## 1. Dual-Mode Philosophy

```mermaid
%%{init: {'theme': 'neutral'}}%%
mindmap
  root((🔀 Dual-Mode))
    🌿 Open-Source Mode
      Groq API demo
      Self-hosted vLLM/TGI
      Llama 3.3 70B
      Qwen 3 32B
      Can self-host anytime
    ☁️ Proprietary Mode
      Render.com
      Gemini API
      Closed-source
      Cannot self-host
      Vendor lock-in
    🔄 Abstraction Layer
      LLM Provider Interface
      Same LangGraph logic
      Feature parity
      Environment configs
```

### Why Dual-Mode?

| Benefit | Open-Source (Groq/Self-Hosted) | Proprietary (Gemini) |
|:--------|:-------------------------------|:---------------------|
| **Models** | Llama, Qwen, Mistral (open) | Gemini (closed) |
| **License** | Apache 2.0, Llama Community | Proprietary |
| **Self-Hosting** | ✅ Full support | ❌ Not possible |
| **Data Privacy** | ✅ On-premises capable | ⚠️ Cloud only |
| **Performance** | 200-300 tok/s (with LPU/GPU) | ~80-120 tok/s |
| **Cost (production)** | Hardware investment | Per-token pricing |
| **Vendor Lock-in** | ✅ None | ⚠️ High |
| **Customization** | ✅ Fine-tune, modify | ❌ Limited |
| **Government Compliance** | ✅ Yes (on-prem) | ⚠️ Maybe |

---

## 2. Architecture Overview

### 2.1 Open-Source Mode Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph opensource["🌿 OPEN-SOURCE DEPLOYMENT"]
        subgraph services["🧠 Services"]
            api["🔌 FastAPI<br/><i>localhost:8000</i>"]
            brain["🧠 LangGraph<br/><i>Agent Orchestrator</i>"]
        end
        
        subgraph data["💾 Data Layer"]
            pg["🐘 PostgreSQL<br/><i>localhost:5432</i>"]
            redis["⚡ Redis<br/><i>localhost:6379</i>"]
        end
        
        api --> brain
        brain --> redis
        brain --> pg
    end
    
    subgraph llm["🤖 LLM Options (choose one)"]
        groq["⚡ Groq API<br/><i>200-300 tok/s</i><br/><i>Open-source models</i>"]
        selfhost["🏢 Self-Hosted<br/><i>vLLM / TGI</i><br/><i>On-premises</i>"]
    end
    
    brain -->|"API Call"| groq
    brain -.->|"Production"| selfhost
    
    subgraph client["📱 Clients"]
        demo["🖥️ Chainlit Demo<br/><i>localhost:8501</i>"]
        mobile["📱 Yonca App"]
    end
    
    demo --> api
    mobile --> api
    
    style opensource fill:#e3f2fd,stroke:#1565c0,stroke-width:3px,color:#0d47a1
    style services fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    style data fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style llm fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
```

**Open-Source Models Available (via Groq or self-hosted):**

| Model | Class | License | Self-Hosting | Use Case |
|:------|:------|:--------|:-------------|:---------|
| **Llama 3.3 70B** | 🏆 Gold Standard | Llama Community | 2× RTX 5090 / H100 | User-facing chat (best Azerbaijani) |
| **Llama 4 Maverick** | 🏆 Gold Standard | Llama Community | 2× RTX 5090 / H100 | Future upgrade path |
| **Qwen 3 32B** | Internal | Apache 2.0 | 1× RTX 5090 / A100 | Math/logic calculations |
| **Llama 3.1 8B** | Baseline | Llama Community | RTX 4090 | Fast responses, prototypes |

> 💡 **Gold Standard (70B)** = Enterprise-grade reasoning. See [15-HARDWARE-JUSTIFICATION.md](15-HARDWARE-JUSTIFICATION.md) for why this matters.

### 2.2 Model Selection Quick Reference

> 🏆 **2026 Gold Standard:** Llama 4 Maverick is a Mixture-of-Experts (MoE) model with 17B active parameters. It replaces the previous two-model stack (Qwen + Llama) with a single, all-in-one solution.

#### TL;DR - Which Model to Use?

| Scenario | Recommended Model | Notes |
|:---------|:------------------|:------|
| **Production (2026)** | `meta-llama/llama-4-maverick-17b-128e-instruct` | ⭐ Gold Standard - single node for all tasks |
| **Language Quality** | `llama-3.3-70b-versatile` | Best Azerbaijani, no Turkish leakage |
| **Math/Logic Only** | `qwen3-32b` | Fast calculations (Turkish leakage risk for chat) |
| **Fallback Only** | `gemini-2.0-flash-exp` | ⚠️ Proprietary, vendor lock-in |

#### Model Comparison (January 2026)

| Model | Speed | Azerbaijani | Math | Vision | Context |
|:------|:------|:------------|:-----|:-------|:--------|
| **llama-4-maverick** | ⚡⚡⚡⚡⚡ (~300 tps) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 128k |
| llama-3.3-70b-versatile | ⚡⚡⚡ (~200 tps) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | 128k |
| qwen3-32b | ⚡⚡⚡⚡⚡ (~280 tps) | ⭐⭐ ⚠️ | ⭐⭐⭐⭐⭐ | ❌ | 32k |

⚠️ = Turkish leakage risk in Azerbaijani output

#### Configuration Examples

```bash
# 2026 Gold Standard: Maverick Mode
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
YONCA_GROQ_API_KEY=gsk_your_key_here

# Legacy Mode (still supported)
YONCA_GROQ_MODEL=llama-3.3-70b-versatile
```

---

## 2.3 Hardware Deployment Options

### Option A: Local Workstation ("The Independent Powerhouse")

```
┌─────────────────────────────────────────────────────────┐
│  💻 LOCAL WORKSTATION (Gold Standard)                   │
├─────────────────────────────────────────────────────────┤
│  GPU:     2× NVIDIA RTX 5090 (64GB total VRAM)         │
│  RAM:     128GB DDR5                                    │
│  Storage: 2TB NVMe SSD                                  │
│  Cost:    ~$6,500 (one-time investment)                │
│  Speed:   15-20 tokens/sec                              │
├─────────────────────────────────────────────────────────┤
│  ✅ Complete data isolation                             │
│  ✅ Break-even vs cloud APIs in ~5 months              │
│  ✅ Perfect for pilot/demo phase                       │
└─────────────────────────────────────────────────────────┘
```

### Option B: Apple Silicon ("The Quiet Office Solution")

```
┌─────────────────────────────────────────────────────────┐
│  🍎 MAC STUDIO M3/M4 ULTRA                              │
├─────────────────────────────────────────────────────────┤
│  Memory:  128GB Unified                                 │
│  Storage: 2TB SSD                                       │
│  Cost:    ~$4,800                                       │
│  Speed:   10-15 tokens/sec                              │
├─────────────────────────────────────────────────────────┤
│  ✅ Whisper-quiet operation                            │
│  ✅ Excellent energy efficiency                        │
│  ✅ 128k context window support                        │
└─────────────────────────────────────────────────────────┘
```

### Option C: AzInCloud ("Sovereign Scaling Path")

```
┌─────────────────────────────────────────────────────────┐
│  ☁️ AZINCLOUD (Baku Data Centers)                       │
├─────────────────────────────────────────────────────────┤
│  Hardware: NVIDIA H100 (80GB VRAM)                      │
│  Location: Baku, Azerbaijan (data sovereignty)         │
│  Cost:     €1.30 - €2.80/hour                          │
│  Speed:    50-100+ tokens/sec                           │
├─────────────────────────────────────────────────────────┤
│  ✅ Data stays in Azerbaijan                           │
│  ✅ Massive scaling capability                         │
│  ✅ High concurrency (thousands of users)              │
└─────────────────────────────────────────────────────────┘
```

---

### 2.4 Proprietary Cloud Mode Architecture (Fallback)

> ⚠️ **Note:** This mode uses closed-source Gemini and should only be used as a fallback when open-source options are unavailable.

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph render["☁️ RENDER.COM"]
        subgraph api_service["🔌 Web Service"]
            api["FastAPI<br/><i>yonca-ai.onrender.com</i>"]
            brain["🧠 LangGraph<br/><i>Agent Orchestrator</i>"]
        end
        
        subgraph managed["🗄️ Managed Services"]
            pg["🐘 PostgreSQL<br/><i>Render Managed</i>"]
            redis["⚡ Redis<br/><i>Render Managed</i>"]
        end
        
        api --> brain
        brain --> pg
        brain --> redis
    end
    
    subgraph google["🌐 Google Cloud"]
        gemini["🔮 Gemini API<br/><i>gemini-2.0-flash</i><br/><i>⚠️ Proprietary</i>"]
    end
    
    brain -->|"API Call"| gemini
    
    subgraph clients["📱 Clients"]
        demo["🖥️ Chainlit Demo"]
        mobile["📱 Yonca App"]
    end
    
    demo --> api
    mobile --> api
    
    style render fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    style google fill:#ffcdd2,stroke:#c62828,color:#b71c1c
    style managed fill:#fff9c4,stroke:#f9a825,color:#5d4037
```

**Limitations of Proprietary Mode:**
- ❌ Cannot self-host Gemini models
- ⚠️ Vendor lock-in to Google
- ⚠️ Data sent to Google servers
- ⚠️ Subject to pricing changes

---

## 3. LLM Provider Abstraction

### 3.1 Provider Interface

```python
# src/yonca/llm/providers/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class LLMMessage(BaseModel):
    """Standard message format."""
    role: str  # system, user, assistant
    content: str

class LLMResponse(BaseModel):
    """Standard response format."""
    content: str
    tokens_used: int
    model: str
    finish_reason: str

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass
```

### 3.2 Groq Provider (Open-Source - Recommended)

```python
# src/yonca/llm/providers/groq.py
import httpx
from typing import AsyncIterator
from .base import LLMProvider, LLMMessage, LLMResponse

class GroqProvider(LLMProvider):
    """
    Groq provider for open-source LLM inference.
    
    Uses open-source models (Llama, Qwen, Mistral) that CAN be self-hosted.
    Groq demonstrates the performance these models achieve with proper infrastructure.
    
    Self-hosting options:
    - vLLM on GPU cluster (8x A100 for Llama 3.3 70B)
    - Groq LPU hardware (on-premises)
    - Text Generation Inference (TGI)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",  # Or self-hosted URL
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        data = response.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=self.model,
            finish_reason=data["choices"][0].get("finish_reason", "stop"),
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    import json
                    data = json.loads(line[6:])
                    if delta := data["choices"][0].get("delta", {}).get("content"):
                        yield delta
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False
```

### 3.3 Gemini Provider (Proprietary - Fallback Only)

```python
# src/yonca/llm/providers/gemini.py
import google.generativeai as genai
from typing import AsyncIterator
from .base import LLMProvider, LLMMessage, LLMResponse

class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider (PROPRIETARY - FALLBACK ONLY).
    
    ⚠️ WARNING: This uses closed-source models that CANNOT be self-hosted.
    Use only when open-source options (Groq) are unavailable.
    
    Limitations:
    - Vendor lock-in to Google
    - Data sent to Google servers
    - Cannot be self-hosted
    - Subject to pricing changes
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
    ):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert to Gemini's format."""
        gemini_messages = []
        system_prompt = None
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg.content]})
        
        # Prepend system prompt to first user message if exists
        if system_prompt and gemini_messages:
            gemini_messages[0]["parts"].insert(0, f"[System]: {system_prompt}\n\n")
        
        return gemini_messages
    
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        chat = self.model.start_chat(history=self._convert_messages(messages[:-1]))
        response = await chat.send_message_async(
            messages[-1].content,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return LLMResponse(
            content=response.text,
            tokens_used=response.usage_metadata.total_token_count if response.usage_metadata else 0,
            model=self.model_name,
            finish_reason="stop",
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        chat = self.model.start_chat(history=self._convert_messages(messages[:-1]))
        response = await chat.send_message_async(
            messages[-1].content,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            stream=True,
        )
        async for chunk in response:
            yield chunk.text
    
    async def health_check(self) -> bool:
        try:
            # Simple health check with minimal prompt
            response = self.model.generate_content("test")
            return True
        except Exception:
            return False
```

### 3.4 Provider Factory

```python
# src/yonca/llm/factory.py
from enum import Enum
from .providers.base import LLMProvider
from .providers.groq import GroqProvider
from .providers.gemini import GeminiProvider

class LLMProviderType(Enum):
    GROQ = "groq"        # Open-source models (recommended)
    GEMINI = "gemini"    # Proprietary fallback

def create_llm_provider(
    provider_type: LLMProviderType,
    **kwargs,
) -> LLMProvider:
    """Factory function to create LLM providers."""
    
    if provider_type == LLMProviderType.GROQ:
        # Open-source models via Groq (or self-hosted)
        return GroqProvider(
            api_key=kwargs["api_key"],
            model=kwargs.get("model", "llama-3.3-70b-versatile"),
            base_url=kwargs.get("base_url", "https://api.groq.com/openai/v1"),
        )
    elif provider_type == LLMProviderType.GEMINI:
        # Proprietary fallback only
        return GeminiProvider(
            api_key=kwargs["api_key"],
            model=kwargs.get("model", "gemini-2.0-flash-exp"),
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
```

---

## 4. Self-Hosting Guide (Production)

For production deployment in Azerbaijan with government compliance, you can self-host the same open-source models.

### Option A: GPU Cluster

**Hardware Requirements:**
```
Production Setup:
- 8x NVIDIA A100 80GB GPUs (for Llama 3.3 70B)
- 4x NVIDIA A100 80GB GPUs (for Qwen 3 32B)
- 2TB RAM
- 10TB NVMe storage
- High-bandwidth networking (InfiniBand)

Cost: ~$150,000-200,000 (one-time)
Performance: 200-300 tokens/sec
```

**Software Stack:**
```bash
# Use vLLM for optimized inference
pip install vllm

# Run Llama 3.3 70B
vllm serve meta-llama/Llama-3.3-70B-Instruct \
    --tensor-parallel-size 8 \
    --max-model-len 4096

# Run Qwen 3 32B
vllm serve Qwen/Qwen3-32B \
    --tensor-parallel-size 4
```

### Option B: Groq LPU (Recommended for Production)

**Groq's Language Processing Units (LPUs)**:
- Purpose-built for LLM inference
- 200-300 tokens/sec per LPU
- Lower power consumption vs GPUs
- Easier deployment and management

**For Azerbaijan Deployment:**
1. Contact Groq for enterprise licensing
2. Deploy LPU cluster on-premises
3. Run open-source models locally
4. Same performance as Groq cloud
```

---

## 5. Environment Configuration

### 5.1 Environment Matrix

| Environment | Mode | LLM Provider | Models | Infrastructure |
|:------------|:-----|:-------------|:-------|:---------------|
| **Dev** | Open-Source | Groq API | Llama 3.3, Qwen 3 | Docker Compose |
| **Staging** | Open-Source | Groq API | Llama 3.3, Qwen 3 | Render/Cloud |
| **Production** | Open-Source | Self-Hosted | Llama 3.3, Qwen 3 | On-Premises |
| **Fallback** | Proprietary | Gemini API | Gemini 2.0 | Cloud only |

### 5.2 Environment Variables

```bash
# .env.open_source - Open-Source Mode (RECOMMENDED)
# ================================================
YONCA_DEPLOYMENT_MODE=open_source

# LLM Configuration (Groq - Open-Source Models)
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_API_KEY=gsk_your_key_here
YONCA_GROQ_MODEL=llama-3.3-70b-versatile

# For self-hosted deployment:
# YONCA_GROQ_BASE_URL=http://your-llm-cluster:8000

# Database
YONCA_DATABASE_URL=postgresql://yonca:password@localhost:5432/yonca

# Redis
YONCA_REDIS_URL=redis://localhost:6379/0

# API
YONCA_API_HOST=0.0.0.0
YONCA_API_PORT=8000
```

```bash
# .env.proprietary - Proprietary Fallback (NOT RECOMMENDED)
# =========================================================
YONCA_DEPLOYMENT_MODE=cloud

# LLM Configuration (Gemini - Proprietary)
# ⚠️ WARNING: Cannot self-host, vendor lock-in
YONCA_LLM_PROVIDER=gemini
YONCA_GEMINI_API_KEY=${GEMINI_API_KEY}
YONCA_GEMINI_MODEL=gemini-2.0-flash-exp

# Database (Render Managed PostgreSQL)
YONCA_DATABASE_URL=${DATABASE_URL}

# Redis (Render Managed)
YONCA_REDIS_URL=${REDIS_URL}

# API
YONCA_API_HOST=0.0.0.0
YONCA_API_PORT=10000
```

---

## 6. Docker Configuration

### 6.1 Open-Source Mode (docker-compose.local.yml)

```yaml
# docker-compose.local.yml
version: '3.9'

services:
  # ================================
  # PostgreSQL - Data Store
  # ================================
  postgres:
    image: postgres:16-alpine
    container_name: yonca-postgres
    environment:
      POSTGRES_USER: yonca
      POSTGRES_PASSWORD: yonca_dev_password
      POSTGRES_DB: yonca_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yonca"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ================================
  # Redis - Cache & Session Store
  # ================================
  redis:
    image: redis:7-alpine
    container_name: yonca-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ================================
  # Yonca API - FastAPI Application
  # ================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: yonca-api
    ports:
      - "8000:8000"
    environment:
      - YONCA_DEPLOYMENT_MODE=open_source
      - YONCA_LLM_PROVIDER=groq
      - YONCA_GROQ_API_KEY=${YONCA_GROQ_API_KEY}
      - YONCA_GROQ_MODEL=llama-3.3-70b-versatile
      - YONCA_DATABASE_URL=postgresql://yonca:yonca_dev_password@postgres:5432/yonca_dev
      - YONCA_REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./prompts:/app/prompts
      - ./tests:/app/tests
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn yonca.api.main:app --host 0.0.0.0 --port 8000 --reload

  # ================================
  # Chainlit Demo UI
  # ================================
  demo:
    build:
      context: ./demo-ui
      dockerfile: Dockerfile
    container_name: yonca-demo
    ports:
      - "8501:8501"
    environment:
      - YONCA_API_URL=http://api:8000
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

> 💡 **Note:** Ollama is no longer needed for local development. We use Groq API (open-source models) for fast iteration. For offline/self-hosted scenarios, deploy vLLM or TGI.

### 5.2 Cloud Mode (render.yaml)

```yaml
# render.yaml - Render Blueprint
services:
  # ================================
  # Yonca API - Main Web Service
  # ================================
  - type: web
    name: yonca-ai
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    branch: main
    plan: starter  # or standard for production
    healthCheckPath: /health
    envVars:
      - key: DEPLOYMENT_MODE
        value: cloud
      - key: LLM_PROVIDER
        value: gemini
      - key: GEMINI_API_KEY
        sync: false  # Set manually in dashboard
      - key: GEMINI_MODEL
        value: gemini-2.0-flash-exp
      - key: DATABASE_URL
        fromDatabase:
          name: yonca-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: yonca-redis
          type: redis
          property: connectionString
      - key: LOG_LEVEL
        value: INFO
      - key: ENVIRONMENT
        value: production

  # ================================
  # Chainlit Demo UI
  # ================================
  - type: web
    name: yonca-demo
    runtime: docker
    dockerfilePath: ./demo-ui/Dockerfile
    dockerContext: ./demo-ui
    branch: main
    plan: starter
    envVars:
      - key: YONCA_API_URL
        fromService:
          name: yonca-ai
          type: web
          property: host

databases:
  # ================================
  # PostgreSQL Database
  # ================================
  - name: yonca-db
    plan: starter  # or standard for production
    databaseName: yonca
    user: yonca

# Redis is configured separately in Render dashboard
```

---

## 7. Feature Parity Matrix

Both modes support identical features:

| Feature | Open-Source | Proprietary | Notes |
|:--------|:------------|:------------|:------|
| **Chat API** | ✅ | ✅ | Same endpoints |
| **Streaming** | ✅ | ✅ | SSE for both |
| **Multi-turn** | ✅ | ✅ | Redis memory |
| **Farm Context** | ✅ | ✅ | PostgreSQL |
| **Rule Validation** | ✅ | ✅ | Same rulebook |
| **Azerbaijani** | ✅ | ✅ | Same prompts |
| **PII Protection** | ✅ | ✅ | Same gateway |
| **Rate Limiting** | ✅ | ✅ | Same logic |
| **Metrics** | ✅ | ✅ | Prometheus |
| **Logging** | ✅ | ✅ | Structured |
| **Self-Hosting** | ✅ | ❌ | Key difference |
| **Vendor Lock-in** | ✅ None | ⚠️ High | Key difference |

---

## 8. Model Selection Guide

### 8.1 Open-Source Models (via Groq or Self-Hosted)

| Model | License | Speed | Azerbaijani | Math | Use Case |
|:------|:--------|:------|:------------|:-----|:---------|
| `llama-3.3-70b-versatile` | Llama Community | 200 tok/s | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Primary chat** |
| `qwen3-32b` | Apache 2.0 | 250 tok/s | ⭐⭐ ⚠️ | ⭐⭐⭐⭐⭐ | **Calculations** |
| `llama-3.1-8b-instant` | Llama Community | 300 tok/s | ⭐⭐⭐ | ⭐⭐⭐ | Fast responses |
| `mixtral-8x7b-32768` | Apache 2.0 | 200 tok/s | ⭐⭐⭐ | ⭐⭐⭐ | Alternative |

⚠️ = Turkish leakage risk (rewrite output with Llama)

### 8.2 Proprietary Models (Fallback Only)

| Model | Speed | Quality | Cost | Self-Host |
|:------|:------|:--------|:-----|:----------|
| `gemini-2.0-flash-exp` | Fast | ⭐⭐⭐⭐ | Low | ❌ No |
| `gemini-1.5-flash` | Fast | ⭐⭐⭐⭐ | Low | ❌ No |
| `gemini-1.5-pro` | Medium | ⭐⭐⭐⭐⭐ | Medium | ❌ No |

---

## 9. Switching Between Modes

### 9.1 Environment Detection

```python
# src/yonca/config.py
from enum import Enum
from pydantic_settings import BaseSettings

class DeploymentMode(str, Enum):
    OPEN_SOURCE = "open_source"  # Open-source models (can self-host)
    CLOUD = "cloud"              # Proprietary fallback

class Settings(BaseSettings):
    # Deployment
    deployment_mode: DeploymentMode = DeploymentMode.OPEN_SOURCE
    
    # LLM Provider
    llm_provider: str = "groq"  # Default to open-source
    
    # Groq (Open-Source - Recommended)
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"  # Or self-hosted
    
    # Gemini (Proprietary - Fallback)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Database
    database_url: str = "postgresql://yonca:password@localhost:5432/yonca"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    @property
    def is_open_source(self) -> bool:
        return self.deployment_mode == DeploymentMode.OPEN_SOURCE
    
    class Config:
        env_prefix = "YONCA_"
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 9.2 Provider Selection

```python
# src/yonca/llm/__init__.py
from .factory import create_llm_provider, LLMProviderType
from ..config import settings

def get_llm_provider():
    """Get the configured LLM provider."""
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("YONCA_GROQ_API_KEY required for Groq provider")
        return create_llm_provider(
            LLMProviderType.GROQ,
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            base_url=settings.groq_base_url,
        )
    elif settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("YONCA_GEMINI_API_KEY required for Gemini provider")
        return create_llm_provider(
            LLMProviderType.GEMINI,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
```

---

## 10. Deployment Commands

### 10.1 Open-Source Development

```bash
# Set your Groq API key
export YONCA_GROQ_API_KEY=gsk_your_key_here

# Start all services
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f api

# Stop services
docker-compose -f docker-compose.local.yml down
```

### 10.2 Self-Hosted Production

```bash
# Point to your self-hosted vLLM/TGI server
export YONCA_GROQ_BASE_URL=http://your-llm-cluster:8000
export YONCA_GROQ_MODEL=meta-llama/Llama-3.3-70B-Instruct

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### 10.3 Proprietary Fallback (Render)

```bash
# Deploy via Render CLI
render blueprint launch

# Or via GitHub integration:
# 1. Connect repo to Render
# 2. Render auto-deploys on push to main
# 3. Set YONCA_GEMINI_API_KEY in Render dashboard
```

---

## 11. Cost Analysis

### 11.1 Open-Source Mode Costs

**Development (Groq API):**
| Component | Free Tier | Paid |
|:----------|:----------|:-----|
| Groq API | 14,400 req/day | ~$10/mo |
| PostgreSQL | $0 (local) | $7/mo (hosted) |
| Redis | $0 (local) | $10/mo (hosted) |
| **Total** | **$0** | **~$27/mo** |

**Production (Self-Hosted):**
| Component | One-time | Monthly | Notes |
|:----------|:---------|:--------|:------|
| GPU Cluster | $150-200k | ~$500 | 8x A100 + 4x A100 |
| Electricity | - | ~$200 | Running 24/7 |
| DevOps | - | ~$2000 | Staff cost |
| **Total** | ~$200k | ~$2700/mo | Full control |

### 11.2 Proprietary Mode Costs (Render + Gemini)

| Component | Free Tier | Starter | Pro |
|:----------|:----------|:--------|:----|
| Web Service | Limited | $7/mo | $25/mo |
| PostgreSQL | - | $7/mo | $25/mo |
| Redis | - | $10/mo | $25/mo |
| Gemini API | Free tier | ~$5/mo | ~$20/mo |
| **Total** | $0 | ~$29/mo | ~$95/mo |

> ⚠️ **Note:** Proprietary mode has lower upfront cost but permanent vendor lock-in.

---

<div align="center">

**📄 Document:** `12-DUAL-MODE-DEPLOYMENT.md`  
**🔄 Next:** [13-IMPLEMENTATION-PLAN.md](13-IMPLEMENTATION-PLAN.md) — Step-by-Step Build Guide

</div>
