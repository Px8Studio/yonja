# 🚀 Yonca AI — DevOps Runbook

> **Purpose:** Define CI/CD pipelines, deployment procedures, environment management, and operational runbooks for the AI Sidecar.

---

## 1. DevOps Overview

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
mindmap
  root((🚀 DevOps))
    🔄 CI/CD
      Build pipeline
      Test automation
      Deploy stages
    🏗️ Environments
      Development
      Staging
      Production
    📦 Artifacts
      Container images
      Model versions
      Config bundles
    🔧 Operations
      Runbooks
      Rollback
      Incident response
```

---

## 2. Environment Strategy

### 2.1 Environment Matrix

| Environment | Purpose | Data | LLM Model | Infrastructure |
|:------------|:--------|:-----|:----------|:---------------|
| **Local** | Developer workstation | Mock/Synthetic | Qwen-3B (lite) | Docker Compose |
| **Dev** | Feature development | Synthetic only | Qwen-7B Q4 | Single node |
| **Staging** | Pre-production testing | Synthetic + load | Qwen-7B Q4 | Prod-like |
| **Production** | Live service | Synthetic (prod) | Qwen-7B Q4 | HA cluster |

### 2.2 Environment Configuration

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
graph LR
    subgraph local["💻 Local"]
        local_api["API<br/><i>localhost:8000</i>"]
        local_db["SQLite<br/><i>synthetic.db</i>"]
    end
    
    subgraph dev["🔧 Development"]
        dev_api["API<br/><i>dev.yonca.ai</i>"]
        dev_db["PostgreSQL<br/><i>dev cluster</i>"]
    end
    
    subgraph staging["🧪 Staging"]
        staging_api["API<br/><i>staging.yonca.ai</i>"]
        staging_db["PostgreSQL<br/><i>replica of prod</i>"]
    end
    
    subgraph prod["🚀 Production"]
        prod_api["API<br/><i>api.yonca.ai</i>"]
        prod_db["PostgreSQL<br/><i>HA cluster</i>"]
    end
    
    local --> dev --> staging --> prod
    
    style local fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style dev fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style staging fill:#ffe0b2,stroke:#ef6c00,color:#e65100
    style prod fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
```

### 2.3 Environment Variables

```bash
# .env.example
# =====================================================
# YONCA AI SIDECAR - ENVIRONMENT CONFIGURATION
# =====================================================

# Environment
ENVIRONMENT=development  # development | staging | production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=["http://localhost:3000"]

# Database
DATABASE_URL=postgresql://yonca:password@localhost:5432/yonca_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# LLM Configuration
LLM_MODEL_PATH=/models/qwen2.5-7b-instruct-q4_k_m.gguf
LLM_CONTEXT_SIZE=4096
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7

# llama.cpp server
LLAMA_SERVER_URL=http://localhost:8080
LLAMA_N_GPU_LAYERS=35

# Authentication
AUTH_ENABLED=true
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
MYGOV_PUBLIC_KEY_URL=https://mygov.az/.well-known/jwks.json

# Observability
LOG_LEVEL=INFO
LOG_FORMAT=json
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
PROMETHEUS_ENABLED=true

# Feature Flags
FEATURE_RAG_ENABLED=true
FEATURE_WEATHER_INTEGRATION=false
FEATURE_PROACTIVE_ALERTS=false

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=30
RATE_LIMIT_BURST=50

# Synthetic Data
SYNTHETIC_DATA_SEED=42
SYNTHETIC_FARMS_COUNT=1000
```

---

## 3. CI/CD Pipeline

### 3.1 Pipeline Overview

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
graph TB
    subgraph trigger["🎯 Triggers"]
        push["Push to branch"]
        pr["Pull Request"]
        tag["Version Tag"]
        manual["Manual Deploy"]
    end
    
    subgraph build["🔨 Build Stage"]
        lint["Lint & Format"]
        typecheck["Type Check"]
        unit["Unit Tests"]
        build_image["Build Image"]
    end
    
    subgraph test["🧪 Test Stage"]
        integration["Integration Tests"]
        golden["Golden Dataset Eval"]
        security["Security Scan"]
    end
    
    subgraph deploy["🚀 Deploy Stage"]
        deploy_dev["Deploy Dev"]
        deploy_staging["Deploy Staging"]
        deploy_prod["Deploy Prod"]
    end
    
    subgraph verify["✅ Verify Stage"]
        smoke["Smoke Tests"]
        e2e["E2E Tests"]
        rollback_check["Rollback Ready"]
    end
    
    push --> lint
    pr --> lint
    lint --> typecheck --> unit --> build_image
    build_image --> integration --> golden --> security
    
    tag --> deploy_staging
    manual --> deploy_prod
    
    deploy_dev --> smoke
    deploy_staging --> e2e
    deploy_prod --> rollback_check
    
    style trigger fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style build fill:#fff9c4,stroke:#f9a825,color:#5d4037
    style test fill:#ffe0b2,stroke:#ef6c00,color:#e65100
    style deploy fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
    style verify fill:#e1bee7,stroke:#7b1fa2,color:#4a148c
```

### 3.2 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: Yonca AI CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================
  # LINT & FORMAT
  # ============================================
  lint:
    name: 🔍 Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install ruff black mypy
      
      - name: Run Ruff (linting)
        run: ruff check src/ tests/
      
      - name: Run Black (formatting)
        run: black --check src/ tests/
      
      - name: Run MyPy (type checking)
        run: mypy src/ --ignore-missing-imports

  # ============================================
  # UNIT TESTS
  # ============================================
  test-unit:
    name: 🧪 Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  # ============================================
  # BUILD DOCKER IMAGE
  # ============================================
  build:
    name: 🐳 Build Image
    runs-on: ubuntu-latest
    needs: test-unit
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix=
      
      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # INTEGRATION TESTS
  # ============================================
  test-integration:
    name: 🔗 Integration Tests
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: yonca
          POSTGRES_PASSWORD: test
          POSTGRES_DB: yonca_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://yonca:test@localhost:5432/yonca_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest tests/integration/ -v --tb=short

  # ============================================
  # GOLDEN DATASET EVALUATION
  # ============================================
  test-golden:
    name: 🎯 Golden Dataset Eval
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Download model (cached)
        uses: actions/cache@v4
        with:
          path: models/
          key: llm-model-qwen-7b-q4
      
      - name: Run golden dataset evaluation
        run: |
          python -m yonca.evaluation.runner \
            --dataset tests/golden/dataset.json \
            --model models/qwen2.5-7b-instruct-q4_k_m.gguf \
            --threshold 0.85 \
            --output eval-results.json
      
      - name: Upload evaluation results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results
          path: eval-results.json

  # ============================================
  # SECURITY SCAN
  # ============================================
  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run dependency check
        run: |
          pip install safety
          safety check -r requirements.txt

  # ============================================
  # DEPLOY TO STAGING
  # ============================================
  deploy-staging:
    name: 🚀 Deploy Staging
    runs-on: ubuntu-latest
    needs: [test-integration, test-golden, security]
    if: github.ref == 'refs/heads/main' || github.event_name == 'release'
    environment:
      name: staging
      url: https://staging.yonca.ai
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging..."
          # kubectl apply -k k8s/overlays/staging/
          # OR
          # docker compose -f docker-compose.staging.yml up -d
      
      - name: Run smoke tests
        run: |
          ./scripts/smoke-test.sh https://staging.yonca.ai
      
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Deployed to staging: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

  # ============================================
  # DEPLOY TO PRODUCTION
  # ============================================
  deploy-production:
    name: 🚀 Deploy Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.event_name == 'release' || github.event.inputs.environment == 'production'
    environment:
      name: production
      url: https://api.yonca.ai
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          echo "Deploying to production..."
          # Blue-green deployment
          # kubectl set image deployment/yonca-sidecar ...
      
      - name: Run production smoke tests
        run: |
          ./scripts/smoke-test.sh https://api.yonca.ai
      
      - name: Create rollback point
        run: |
          echo "ROLLBACK_IMAGE=${{ needs.build.outputs.image-tag }}" >> $GITHUB_OUTPUT
      
      - name: Notify team
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Production deployment complete: ${{ github.ref_name }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 4. Docker Configuration

### 4.1 Production Dockerfile

```dockerfile
# Dockerfile
# Multi-stage build for Yonca AI Sidecar

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 yonca

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=yonca:yonca src/ ./src/
COPY --chown=yonca:yonca config/ ./config/
COPY --chown=yonca:yonca prompts/ ./prompts/

# Create directories
RUN mkdir -p /app/logs /app/models && chown -R yonca:yonca /app

# Switch to non-root user
USER yonca

# Environment
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    LOG_FORMAT=json

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run
CMD ["python", "-m", "uvicorn", "yonca.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ============================================
  # YONCA API
  # ============================================
  yonca-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://yonca:password@postgres:5432/yonca
      - REDIS_URL=redis://redis:6379/0
      - LLAMA_SERVER_URL=http://llama:8080
      - LOG_LEVEL=DEBUG
    volumes:
      - ./src:/app/src:ro
      - ./config:/app/config:ro
      - ./prompts:/app/prompts:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      llama:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - yonca-network

  # ============================================
  # LLAMA.CPP SERVER
  # ============================================
  llama:
    image: ghcr.io/ggerganov/llama.cpp:server
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models:ro
    command: >
      --model /models/qwen2.5-7b-instruct-q4_k_m.gguf
      --host 0.0.0.0
      --port 8080
      --ctx-size 4096
      --n-gpu-layers 35
      --parallel 2
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - yonca-network

  # ============================================
  # POSTGRESQL
  # ============================================
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: yonca
      POSTGRES_PASSWORD: password
      POSTGRES_DB: yonca
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yonca"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - yonca-network

  # ============================================
  # REDIS
  # ============================================
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - yonca-network

volumes:
  postgres-data:
  redis-data:

networks:
  yonca-network:
    driver: bridge
```

---

## 5. Kubernetes Deployment

### 5.1 Deployment Manifest

```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yonca-sidecar
  labels:
    app: yonca-sidecar
    component: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: yonca-sidecar
  template:
    metadata:
      labels:
        app: yonca-sidecar
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: yonca-sidecar
      
      initContainers:
        # Wait for dependencies
        - name: wait-for-postgres
          image: busybox:1.36
          command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 2; done']
        
        # Download model if not cached
        - name: download-model
          image: curlimages/curl:8.5.0
          command:
            - sh
            - -c
            - |
              if [ ! -f /models/qwen2.5-7b-instruct-q4_k_m.gguf ]; then
                curl -L -o /models/qwen2.5-7b-instruct-q4_k_m.gguf \
                  "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
              fi
          volumeMounts:
            - name: model-storage
              mountPath: /models
      
      containers:
        - name: yonca-sidecar
          image: ghcr.io/zekalab/yonca-sidecar:latest
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 8000
          
          envFrom:
            - configMapRef:
                name: yonca-config
            - secretRef:
                name: yonca-secrets
          
          resources:
            requests:
              memory: "16Gi"
              cpu: "4"
              nvidia.com/gpu: "1"
            limits:
              memory: "32Gi"
              cpu: "8"
              nvidia.com/gpu: "1"
          
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 60
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          
          volumeMounts:
            - name: model-storage
              mountPath: /models
              readOnly: true
            - name: prompts
              mountPath: /app/prompts
              readOnly: true
      
      volumes:
        - name: model-storage
          persistentVolumeClaim:
            claimName: model-pvc
        - name: prompts
          configMap:
            name: yonca-prompts
      
      tolerations:
        - key: "nvidia.com/gpu"
          operator: "Exists"
          effect: "NoSchedule"
      
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: node.kubernetes.io/instance-type
                    operator: In
                    values:
                      - g4dn.xlarge
                      - g4dn.2xlarge
```

### 5.2 Service and Ingress

```yaml
# k8s/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: yonca-sidecar
  labels:
    app: yonca-sidecar
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
      name: http
  selector:
    app: yonca-sidecar
---
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: yonca-sidecar
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
    - hosts:
        - api.yonca.ai
      secretName: yonca-tls
  rules:
    - host: api.yonca.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: yonca-sidecar
                port:
                  number: 80
```

---

## 6. Rollback Procedures

### 6.1 Rollback Decision Matrix

| Symptom | Severity | Action | Rollback? |
|:--------|:---------|:-------|:----------|
| Error rate > 5% | **Critical** | Immediate rollback | ✅ Yes |
| P95 latency > 10s | **High** | Investigate 5 min | Maybe |
| Memory leak detected | **High** | Drain and replace pods | ✅ Yes |
| Single pod crash | **Low** | Monitor auto-recovery | ❌ No |
| Golden test failure | **Medium** | Evaluate impact | Maybe |

### 6.2 Rollback Commands

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

NAMESPACE="${NAMESPACE:-yonca}"
DEPLOYMENT="${DEPLOYMENT:-yonca-sidecar}"

echo "🔄 Rolling back deployment: $DEPLOYMENT"

# Get current revision
CURRENT_REVISION=$(kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE | tail -2 | head -1 | awk '{print $1}')
echo "Current revision: $CURRENT_REVISION"

# Rollback to previous revision
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollback to complete
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

# Verify
NEW_REVISION=$(kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE | tail -2 | head -1 | awk '{print $1}')
echo "✅ Rolled back from revision $CURRENT_REVISION to $NEW_REVISION"

# Run smoke tests
./scripts/smoke-test.sh "https://api.yonca.ai"

echo "🎉 Rollback complete!"
```

### 6.3 Rollback to Specific Version

```bash
# Rollback to specific revision
kubectl rollout undo deployment/yonca-sidecar --to-revision=5

# Rollback to specific image tag
kubectl set image deployment/yonca-sidecar \
  yonca-sidecar=ghcr.io/zekalab/yonca-sidecar:v1.2.3

# View rollout history
kubectl rollout history deployment/yonca-sidecar

# Describe specific revision
kubectl rollout history deployment/yonca-sidecar --revision=5
```

---

## 7. Operational Runbooks

### 7.1 Runbook: High CPU Usage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔥 RUNBOOK: HIGH CPU USAGE                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ TRIGGER: CPU > 85% for > 5 minutes                                         │
│ SEVERITY: High                                                              │
│                                                                             │
│ STEPS:                                                                      │
│                                                                             │
│ 1. Check current pod status                                                 │
│    $ kubectl get pods -n yonca -o wide                                     │
│                                                                             │
│ 2. Check resource usage                                                     │
│    $ kubectl top pods -n yonca                                             │
│                                                                             │
│ 3. Check for stuck requests                                                 │
│    $ curl -s http://localhost:8000/metrics | grep yonca_requests_active   │
│                                                                             │
│ 4. If single pod affected:                                                  │
│    - Check pod logs: kubectl logs <pod> -n yonca --tail=100               │
│    - Restart pod: kubectl delete pod <pod> -n yonca                       │
│                                                                             │
│ 5. If all pods affected:                                                    │
│    - Check for traffic spike in Grafana                                    │
│    - Scale up: kubectl scale deployment/yonca-sidecar --replicas=5        │
│    - Enable rate limiting if not already active                            │
│                                                                             │
│ 6. If persists after scaling:                                               │
│    - Check for inference bottleneck (LLM server)                           │
│    - Consider enabling degradation mode                                     │
│                                                                             │
│ ESCALATION: If unresolved after 15 min, page on-call engineer             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Runbook: Database Connection Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔥 RUNBOOK: DATABASE CONNECTION ISSUES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ TRIGGER: DB connection errors > 10/min                                      │
│ SEVERITY: Critical                                                          │
│                                                                             │
│ IMMEDIATE ACTIONS:                                                          │
│                                                                             │
│ 1. Verify database is reachable                                             │
│    $ psql -h $DB_HOST -U yonca -c "SELECT 1"                               │
│                                                                             │
│ 2. Check connection pool exhaustion                                         │
│    $ curl -s http://localhost:8000/metrics | grep db_pool                  │
│                                                                             │
│ 3. Check for long-running queries                                           │
│    $ psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active'"       │
│                                                                             │
│ 4. If pool exhausted:                                                       │
│    - Increase pool size in config                                          │
│    - Restart pods: kubectl rollout restart deployment/yonca-sidecar       │
│                                                                             │
│ 5. If database overloaded:                                                  │
│    - Check slow query log                                                   │
│    - Terminate long queries: SELECT pg_terminate_backend(<pid>)            │
│    - Consider read replica for synthetic data queries                       │
│                                                                             │
│ FALLBACK: Enable synthetic data cache-only mode                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Runbook: LLM Inference Slow/Failing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔥 RUNBOOK: LLM INFERENCE SLOW/FAILING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ TRIGGER: LLM latency > 5s P95 or error rate > 2%                           │
│ SEVERITY: High                                                              │
│                                                                             │
│ DIAGNOSIS:                                                                  │
│                                                                             │
│ 1. Check llama.cpp server health                                            │
│    $ curl http://llama-server:8080/health                                  │
│                                                                             │
│ 2. Check GPU utilization                                                    │
│    $ nvidia-smi                                                             │
│                                                                             │
│ 3. Check inference queue depth                                              │
│    $ curl http://llama-server:8080/metrics | grep queue                    │
│                                                                             │
│ REMEDIATION:                                                                │
│                                                                             │
│ A. If GPU memory exhausted:                                                 │
│    - Reduce batch size / parallel requests                                  │
│    - Restart llama server                                                   │
│                                                                             │
│ B. If queue backed up:                                                      │
│    - Scale llama server instances                                           │
│    - Enable request shedding                                                │
│                                                                             │
│ C. If hardware failure:                                                     │
│    - Failover to CPU-only inference (slower)                               │
│    - Activate degradation mode (rules-only responses)                       │
│                                                                             │
│ DEGRADATION COMMAND:                                                        │
│ $ kubectl set env deployment/yonca-sidecar DEGRADATION_LEVEL=rules_only   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Model Versioning

### 8.1 Model Registry

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#1a1a1a', 'lineColor': '#424242'}}}%%
graph TB
    subgraph registry["📦 Model Registry"]
        v1["v1.0.0<br/><i>Qwen2.5-7B Q4_K_M</i>"]
        v2["v1.1.0<br/><i>+ Agricultural fine-tune</i>"]
        v3["v1.2.0<br/><i>+ Azerbaijani boost</i>"]
    end
    
    subgraph deploy["🚀 Deployments"]
        prod["Production<br/><i>v1.1.0</i>"]
        staging["Staging<br/><i>v1.2.0</i>"]
        dev["Development<br/><i>v1.2.0</i>"]
    end
    
    v1 -.-> prod
    v2 --> prod
    v3 --> staging
    v3 --> dev
    
    style registry fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    style deploy fill:#c8e6c9,stroke:#2e7d32,color:#1b5e20
```

### 8.2 Model Versioning Schema

```yaml
# model-registry/models.yaml
models:
  - name: yonca-base
    version: 1.0.0
    base_model: Qwen2.5-7B-Instruct
    quantization: Q4_K_M
    file: qwen2.5-7b-instruct-q4_k_m.gguf
    size_gb: 4.5
    checksum: sha256:abc123...
    created: 2026-01-10
    status: deprecated
    
  - name: yonca-agri
    version: 1.1.0
    base_model: Qwen2.5-7B-Instruct
    fine_tune: agricultural-az
    quantization: Q4_K_M
    file: yonca-agri-v1.1.0.gguf
    size_gb: 4.5
    checksum: sha256:def456...
    created: 2026-01-15
    status: production
    eval_score: 0.91
    
  - name: yonca-agri-az
    version: 1.2.0
    base_model: Qwen2.5-7B-Instruct
    fine_tune: agricultural-az-enhanced
    quantization: Q4_K_M
    file: yonca-agri-az-v1.2.0.gguf
    size_gb: 4.5
    checksum: sha256:ghi789...
    created: 2026-01-17
    status: staging
    eval_score: 0.93
```

---

## 9. Secrets Management

### 9.1 Secret Structure

```yaml
# k8s/base/secrets.yaml (encrypted with sops)
apiVersion: v1
kind: Secret
metadata:
  name: yonca-secrets
type: Opaque
stringData:
  JWT_SECRET: ENC[AES256_GCM,data:...,type:str]
  DATABASE_PASSWORD: ENC[AES256_GCM,data:...,type:str]
  REDIS_PASSWORD: ENC[AES256_GCM,data:...,type:str]
  MYGOV_CLIENT_SECRET: ENC[AES256_GCM,data:...,type:str]
  SLACK_WEBHOOK: ENC[AES256_GCM,data:...,type:str]
```

### 9.2 Secret Rotation

```bash
#!/bin/bash
# scripts/rotate-secrets.sh

# Rotate JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 32)
kubectl create secret generic yonca-secrets-new \
  --from-literal=JWT_SECRET=$NEW_JWT_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# Rolling restart to pick up new secrets
kubectl rollout restart deployment/yonca-sidecar -n yonca

# Verify
kubectl rollout status deployment/yonca-sidecar -n yonca

echo "✅ Secret rotation complete"
```

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

| Component | Backup Frequency | Retention | Method |
|:----------|:-----------------|:----------|:-------|
| **PostgreSQL** | Every 6 hours | 30 days | pg_dump to S3 |
| **Redis** | Every hour | 7 days | RDB snapshots |
| **Model files** | On release | Forever | Model registry |
| **Configs** | On change | Git history | Git |
| **Secrets** | On change | Encrypted backup | SOPS + S3 |

### 10.2 Recovery Time Objectives

| Scenario | RTO | RPO | Recovery Steps |
|:---------|:----|:----|:---------------|
| **Pod failure** | 1 min | 0 | Auto-restart |
| **Node failure** | 5 min | 0 | Pod rescheduling |
| **Database corruption** | 30 min | 6 hours | Restore from backup |
| **Total cluster loss** | 4 hours | 6 hours | Full rebuild |

### 10.3 Recovery Procedure

```bash
#!/bin/bash
# scripts/disaster-recovery.sh

echo "🔄 Starting disaster recovery..."

# 1. Restore PostgreSQL
echo "📦 Restoring database..."
LATEST_BACKUP=$(aws s3 ls s3://yonca-backups/postgres/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://yonca-backups/postgres/$LATEST_BACKUP ./backup.sql.gz
gunzip backup.sql.gz
psql -h $DB_HOST -U yonca -d yonca < backup.sql

# 2. Restore Redis
echo "📦 Restoring Redis..."
LATEST_RDB=$(aws s3 ls s3://yonca-backups/redis/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://yonca-backups/redis/$LATEST_RDB ./dump.rdb
redis-cli -h $REDIS_HOST DEBUG RELOAD

# 3. Deploy application
echo "🚀 Deploying application..."
kubectl apply -k k8s/overlays/production/

# 4. Verify
echo "✅ Running smoke tests..."
./scripts/smoke-test.sh https://api.yonca.ai

echo "🎉 Disaster recovery complete!"
```

---

<div align="center">

**📄 Document:** `10-DEVOPS-RUNBOOK.md`  
**⬅️ Previous:** [09-PERFORMANCE-SLA.md](09-PERFORMANCE-SLA.md) — Performance & SLA  
**➡️ Next:** [11-DEMO-UI-SPEC.md](11-DEMO-UI-SPEC.md) — Demo UI Specification

</div>
