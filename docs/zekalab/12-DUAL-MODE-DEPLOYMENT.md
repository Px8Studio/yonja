# 🔀 Yonca AI — Dual-Mode Deployment Architecture

> **Purpose:** Define the dual-mode deployment strategy supporting both **Local** (Docker + local LLMs) and **Cloud** (Docker on Render + Gemini API) deployments.

---

## 1. Dual-Mode Philosophy

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
mindmap
  root((🔀 Dual-Mode))
    🏠 Local Mode
      Docker Compose
      Ollama/llama.cpp
      Qwen3-4B GGUF
      SQLite/PostgreSQL
      Full offline capability
    ☁️ Cloud Mode
      Render.com
      Gemini API
      PostgreSQL managed
      Redis managed
      Scalable & reliable
    🔄 Abstraction Layer
      LLM Provider Interface
      Same LangGraph logic
      Feature parity
      Environment configs
```

### Why Dual-Mode?

| Benefit | Local Mode | Cloud Mode |
|:--------|:-----------|:-----------|
| **Cost** | No API fees | Pay-per-use |
| **Privacy** | 100% on-premise | Data leaves local |
| **Latency** | GPU-dependent | ~1-2s API latency |
| **Availability** | Self-managed | 99.9% SLA |
| **Scaling** | Manual | Auto-scale |
| **Development** | Rapid iteration | Production-ready |
| **Rural Use** | Works offline | Requires internet |

---

## 2. Architecture Overview

### 2.1 Local Mode Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
graph TB
    subgraph local["🏠 LOCAL DEPLOYMENT (Docker Compose)"]
        subgraph services["🧠 Services"]
            api["🔌 FastAPI<br/><i>localhost:8000</i>"]
            brain["🧠 LangGraph<br/><i>Agent Orchestrator</i>"]
            ollama["🤖 Ollama<br/><i>Qwen3-4B</i>"]
        end
        
        subgraph data["💾 Data Layer"]
            pg["🐘 PostgreSQL<br/><i>localhost:5432</i>"]
            redis["⚡ Redis<br/><i>localhost:6379</i>"]
        end
        
        api --> brain
        brain --> ollama
        brain --> redis
        brain --> pg
    end
    
    subgraph client["📱 Clients"]
        demo["🖥️ Chainlit Demo<br/><i>localhost:8501</i>"]
        mobile["📱 Yonca App"]
    end
    
    demo --> api
    mobile --> api
    
    style local fill:#e3f2fd,stroke:#1565c0,stroke-width:3px,color:#0d47a1
    style services fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    style data fill:#fff9c4,stroke:#f9a825,color:#5d4037
```

### 2.2 Cloud Mode Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
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
        gemini["🔮 Gemini API<br/><i>gemini-2.0-flash</i>"]
    end
    
    brain -->|"API Call"| gemini
    
    subgraph clients["📱 Clients"]
        demo["🖥️ Chainlit Demo"]
        mobile["📱 Yonca App"]
    end
    
    demo --> api
    mobile --> api
    
    style render fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#1b5e20
    style google fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style managed fill:#fff9c4,stroke:#f9a825,color:#5d4037
```

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

### 3.2 Ollama Provider (Local)

```python
# src/yonca/llm/providers/ollama.py
import httpx
from typing import AsyncIterator
from .base import LLMProvider, LLMMessage, LLMResponse

class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:4b",
    ):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [m.model_dump() for m in messages],
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": False,
            },
        )
        data = response.json()
        return LLMResponse(
            content=data["message"]["content"],
            tokens_used=data.get("eval_count", 0),
            model=self.model,
            finish_reason="stop",
        )
    
    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [m.model_dump() for m in messages],
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data:
                        yield data["message"]["content"]
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
```

### 3.3 Gemini Provider (Cloud)

```python
# src/yonca/llm/providers/gemini.py
import google.generativeai as genai
from typing import AsyncIterator
from .base import LLMProvider, LLMMessage, LLMResponse

class GeminiProvider(LLMProvider):
    """Google Gemini API provider for cloud deployment."""
    
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
from .providers.ollama import OllamaProvider
from .providers.gemini import GeminiProvider

class LLMProviderType(Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"

def create_llm_provider(
    provider_type: LLMProviderType,
    **kwargs,
) -> LLMProvider:
    """Factory function to create LLM providers."""
    
    if provider_type == LLMProviderType.OLLAMA:
        return OllamaProvider(
            base_url=kwargs.get("base_url", "http://localhost:11434"),
            model=kwargs.get("model", "qwen3:4b"),
        )
    elif provider_type == LLMProviderType.GEMINI:
        return GeminiProvider(
            api_key=kwargs["api_key"],
            model=kwargs.get("model", "gemini-2.0-flash-exp"),
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
```

---

## 4. Environment Configuration

### 4.1 Environment Matrix

| Environment | Mode | LLM Provider | Database | Deployment |
|:------------|:-----|:-------------|:---------|:-----------|
| **Local Dev** | Local | Ollama (Qwen3-4B) | SQLite | Docker Compose |
| **Local Full** | Local | Ollama (Qwen3-4B) | PostgreSQL | Docker Compose |
| **Cloud Dev** | Cloud | Gemini Flash | PostgreSQL | Render Free |
| **Cloud Prod** | Cloud | Gemini Flash | PostgreSQL HA | Render Pro |

### 4.2 Environment Variables

```bash
# .env.local - Local Development
# ================================================
DEPLOYMENT_MODE=local

# LLM Configuration (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen3:4b

# Database (SQLite for simplicity)
DATABASE_URL=sqlite:///./data/yonca.db

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
```

```bash
# .env.cloud - Cloud Deployment (Render)
# ================================================
DEPLOYMENT_MODE=cloud

# LLM Configuration (Gemini)
LLM_PROVIDER=gemini
GEMINI_API_KEY=${GEMINI_API_KEY}  # Set in Render secrets
GEMINI_MODEL=gemini-2.0-flash-exp

# Database (Render Managed PostgreSQL)
DATABASE_URL=${DATABASE_URL}  # Provided by Render

# Redis (Render Managed)
REDIS_URL=${REDIS_URL}  # Provided by Render

# API
API_HOST=0.0.0.0
API_PORT=10000  # Render default
```

---

## 5. Docker Configuration

### 5.1 Local Mode (docker-compose.local.yml)

```yaml
# docker-compose.local.yml
version: '3.9'

services:
  # ================================
  # Ollama - Local LLM Server
  # ================================
  ollama:
    image: ollama/ollama:latest
    container_name: yonca-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # For CPU-only, remove deploy section
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5

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
      - DEPLOYMENT_MODE=local
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=qwen3:4b
      - DATABASE_URL=postgresql://yonca:yonca_dev_password@postgres:5432/yonca_dev
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./prompts:/app/prompts
      - ./tests:/app/tests
    depends_on:
      ollama:
        condition: service_healthy
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
  ollama_data:
  postgres_data:
  redis_data:
```

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

## 6. Feature Parity Matrix

Both modes should support identical features:

| Feature | Local Mode | Cloud Mode | Notes |
|:--------|:-----------|:-----------|:------|
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

---

## 7. Model Selection Guide

### 7.1 Local Mode Models

| Model | Size | RAM Required | Quality | Speed | Recommendation |
|:------|:-----|:-------------|:--------|:------|:---------------|
| `qwen3:4b` | 2.6 GB | 5 GB | ⭐⭐⭐⭐ | Fast | **Recommended** |
| `qwen3:1.7b` | 1.2 GB | 3 GB | ⭐⭐⭐ | Very Fast | Edge/low memory |
| `llama3.2:3b` | 2 GB | 4 GB | ⭐⭐⭐ | Fast | Alternative |

### 7.2 Cloud Mode Models

| Model | Context | Quality | Cost | Speed | Recommendation |
|:------|:--------|:--------|:-----|:------|:---------------|
| `gemini-2.0-flash-exp` | 1M | ⭐⭐⭐⭐ | Low | Fast | **Recommended** |
| `gemini-1.5-flash` | 1M | ⭐⭐⭐⭐ | Low | Fast | Stable |
| `gemini-1.5-pro` | 2M | ⭐⭐⭐⭐⭐ | Medium | Medium | Complex queries |

---

## 8. Switching Between Modes

### 8.1 Environment Detection

```python
# src/yonca/config.py
from enum import Enum
from pydantic_settings import BaseSettings

class DeploymentMode(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"

class Settings(BaseSettings):
    # Deployment
    deployment_mode: DeploymentMode = DeploymentMode.LOCAL
    
    # LLM Provider
    llm_provider: str = "ollama"
    
    # Ollama (Local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    
    # Gemini (Cloud)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Database
    database_url: str = "sqlite:///./data/yonca.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 8.2 Provider Selection

```python
# src/yonca/llm/__init__.py
from .factory import create_llm_provider, LLMProviderType
from ..config import settings

def get_llm_provider():
    """Get the configured LLM provider."""
    if settings.llm_provider == "ollama":
        return create_llm_provider(
            LLMProviderType.OLLAMA,
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    elif settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY required for Gemini provider")
        return create_llm_provider(
            LLMProviderType.GEMINI,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
```

---

## 9. Deployment Commands

### 9.1 Local Development

```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Pull Ollama model (first time only)
docker exec -it yonca-ollama ollama pull qwen3:4b

# View logs
docker-compose -f docker-compose.local.yml logs -f api

# Stop services
docker-compose -f docker-compose.local.yml down
```

### 9.2 Cloud Deployment (Render)

```bash
# Deploy via Render CLI
render blueprint launch

# Or via GitHub integration:
# 1. Connect repo to Render
# 2. Render auto-deploys on push to main
# 3. Set GEMINI_API_KEY in Render dashboard
```

---

## 10. Cost Analysis

### 10.1 Local Mode Costs

| Component | One-time | Monthly | Notes |
|:----------|:---------|:--------|:------|
| GPU (RTX 3060) | $300 | - | Optional, speeds up 3x |
| Electricity | - | ~$5 | Running 24/7 |
| **Total** | $300 | ~$5 | After initial investment |

### 10.2 Cloud Mode Costs (Render)

| Component | Free Tier | Starter | Pro |
|:----------|:----------|:--------|:----|
| Web Service | Limited | $7/mo | $25/mo |
| PostgreSQL | - | $7/mo | $25/mo |
| Redis | - | $10/mo | $25/mo |
| **Subtotal** | $0 | $24/mo | $75/mo |
| Gemini API | Free tier | ~$5/mo | ~$20/mo |
| **Total** | $0 | ~$29/mo | ~$95/mo |

---

<div align="center">

**📄 Document:** `12-DUAL-MODE-DEPLOYMENT.md`  
**🔄 Next:** [13-IMPLEMENTATION-PLAN.md](13-IMPLEMENTATION-PLAN.md) — Step-by-Step Build Guide

</div>
