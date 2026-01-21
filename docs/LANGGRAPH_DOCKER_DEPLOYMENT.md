# LangGraph Dev Server Docker Deployment

## Overview

The LangGraph Dev Server can now be deployed as a Docker container for production-like testing and scalable deployments.

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start LangGraph Dev Server + dependencies
docker-compose -f docker-compose.local.yml --profile langgraph up -d

# Check status
docker-compose -f docker-compose.local.yml ps

# View logs
docker-compose -f docker-compose.local.yml logs -f langgraph

# Stop
docker-compose -f docker-compose.local.yml down
```

### Option 2: Standalone Docker

```bash
# Build image
docker build -f Dockerfile.langgraph -t yonca-langgraph:latest .

# Run container
docker run -d \
  --name yonca-langgraph \
  -p 2024:2024 \
  -e PYTHONPATH=/app/src \
  -e DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@host.docker.internal:5433/yonca \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/src:/app/src \
  yonca-langgraph:latest

# Check logs
docker logs -f yonca-langgraph

# Stop
docker stop yonca-langgraph && docker rm yonca-langgraph
```

## Docker Compose Configuration

### Service Definition

**File**: `docker-compose.local.yml`

```yaml
services:
  langgraph:
    build:
      context: .
      dockerfile: Dockerfile.langgraph
    container_name: yonca-langgraph
    ports:
      - "2024:2024"
    volumes:
      - ./src:/app/src              # Hot reload support
      - ./langgraph.json:/app/langgraph.json
    environment:
      # Critical: PYTHONPATH for module imports
      - PYTHONPATH=/app/src

      # Server settings
      - LANGGRAPH_DEV_HOST=0.0.0.0
      - LANGGRAPH_DEV_PORT=2024
      - LANGGRAPH_API_LOG_LEVEL=INFO

      # LLM provider
      - LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=qwen3:4b

      # Database & Redis
      - DATABASE_URL=postgresql+asyncpg://yonca:yonca_dev_password@postgres:5432/yonca
      - REDIS_URL=redis://redis:6379/0

      # Observability
      - LANGFUSE_ENABLED=true
      - LANGFUSE_HOST=http://langfuse-server:3000
    depends_on:
      - postgres
      - redis
      - ollama
    profiles:
      - langgraph  # Optional service
```

### Profiles

The service uses **Docker Compose profiles** for optional deployment:

```bash
# Default services (no LangGraph)
docker-compose -f docker-compose.local.yml up -d

# With LangGraph Dev Server
docker-compose -f docker-compose.local.yml --profile langgraph up -d

# Full stack (all services)
docker-compose -f docker-compose.local.yml --profile demo --profile langgraph up -d
```

## Dockerfile

**File**: `Dockerfile.langgraph`

### Key Features

1. **Base Image**: `python:3.11-slim`
2. **Dependencies**: Installs from `requirements.txt`
3. **LangGraph CLI**: Explicitly installs `langgraph-cli`
4. **Source Code**: Copies `src/` and `langgraph.json`
5. **Environment**: Sets `PYTHONPATH=/app/src`
6. **Health Check**: `curl http://localhost:2024/health`
7. **Command**: `langgraph dev --host 0.0.0.0 --port 2024`

### Build Stages

```dockerfile
# Single-stage build
FROM python:3.11-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y gcc g++ git curl

# Install Python deps
COPY requirements.txt pyproject.toml ./
RUN pip install -r requirements.txt
RUN pip install langgraph-cli

# Copy source
COPY src/ ./src/
COPY langgraph.json ./

# Set env
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 2024

# Health check
HEALTHCHECK CMD curl -f http://localhost:2024/health || exit 1

# Run
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"]
```

## Networking

### Internal Docker Network

Services communicate via Docker network names:

```yaml
networks:
  yonca-network:
    driver: bridge
```

| Service | Internal URL | External URL |
|---------|-------------|--------------|
| LangGraph | `http://langgraph:2024` | `http://localhost:2024` |
| PostgreSQL | `postgres:5432` | `localhost:5433` |
| Redis | `redis:6379` | `localhost:6379` |
| Ollama | `http://ollama:11434` | `http://localhost:11434` |
| Langfuse | `http://langfuse-server:3000` | `http://localhost:3001` |

### Host Access

From **outside Docker** (e.g., Chainlit running on host):

```bash
# LangGraph Dev Server
curl http://localhost:2024/health

# From Chainlit
export YONCA_API_URL=http://localhost:8000
export INTEGRATION_MODE=api
chainlit run app.py
```

From **inside Docker** (e.g., FastAPI container):

```python
# Use internal network names
langgraph_url = "http://langgraph:2024"
```

## Usage Scenarios

### Scenario 1: Local Development (No Docker)

```bash
# VS Code tasks or PowerShell
$env:PYTHONPATH = ".\src"
.\.venv\Scripts\langgraph.exe dev
```

**Best for**: Fast iteration, debugging

### Scenario 2: Docker Development

```bash
# Docker Compose with hot reload
docker-compose -f docker-compose.local.yml --profile langgraph up -d

# View logs
docker-compose logs -f langgraph
```

**Best for**: Testing containerized deployment, multi-service integration

### Scenario 3: Production Testing

```bash
# Build production image
docker build -f Dockerfile.langgraph -t yonca-langgraph:prod .

# Run with production config
docker run -d \
  --name yonca-langgraph-prod \
  -p 2024:2024 \
  -e LANGGRAPH_API_LOG_LEVEL=WARNING \
  -e DATABASE_URL=$PROD_DATABASE_URL \
  yonca-langgraph:prod
```

**Best for**: Load testing, performance validation

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `PYTHONPATH` | Python module search path | `/app/src` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGGRAPH_DEV_HOST` | Bind host | `0.0.0.0` |
| `LANGGRAPH_DEV_PORT` | Bind port | `2024` |
| `LANGGRAPH_API_LOG_LEVEL` | Log verbosity | `INFO` |
| `LLM_PROVIDER` | LLM provider | `ollama` |
| `OLLAMA_BASE_URL` | Ollama URL | `http://ollama:11434` |
| `LANGFUSE_ENABLED` | Enable tracing | `true` |

## Volumes

### Source Code (Development)

```yaml
volumes:
  - ./src:/app/src
  - ./langgraph.json:/app/langgraph.json
```

**Effect**: Changes to graph code trigger auto-reload

### Production (No Volumes)

```yaml
# No volumes - bake code into image
```

**Effect**: Immutable deployment, no hot reload

## Health Checks

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:2024/health || exit 1
```

### Docker Compose Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:2024/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Manual Health Check

```bash
# From host
curl http://localhost:2024/health

# From Docker network
docker exec yonca-langgraph curl http://localhost:2024/health

# Expected response
{"status": "healthy"}
```

## Troubleshooting

### Container Won't Start

**Symptom**:
```
Error: ModuleNotFoundError: No module named 'yonca'
```

**Solution**:
```bash
# Check PYTHONPATH is set
docker exec yonca-langgraph env | grep PYTHONPATH

# Should output: PYTHONPATH=/app/src
```

### Port Conflict

**Symptom**:
```
Error: bind: address already in use
```

**Solution**:
```bash
# Stop existing process
docker stop yonca-langgraph

# Or change port mapping
# In docker-compose.local.yml:
ports:
  - "2025:2024"  # Use different external port
```

### Dependencies Not Found

**Symptom**:
```
ImportError: cannot import name 'State' from 'yonca.agent.state'
```

**Solution**:
```bash
# Rebuild image with updated deps
docker-compose -f docker-compose.local.yml build --no-cache langgraph

# Restart
docker-compose -f docker-compose.local.yml up -d langgraph
```

### Database Connection Failed

**Symptom**:
```
asyncpg.exceptions.InvalidCatalogNameError: database "yonca" does not exist
```

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Run migrations
docker-compose exec api alembic upgrade head
```

## Monitoring

### View Logs

```bash
# Real-time logs
docker-compose -f docker-compose.local.yml logs -f langgraph

# Last 50 lines
docker-compose logs --tail=50 langgraph

# Logs since timestamp
docker-compose logs --since=2024-01-22T10:00:00 langgraph
```

### Inspect Container

```bash
# Container details
docker inspect yonca-langgraph

# Resource usage
docker stats yonca-langgraph

# Execute commands
docker exec -it yonca-langgraph bash
```

### LangSmith Traces

If LangSmith is enabled:

```bash
# Check environment
docker exec yonca-langgraph env | grep LANGSMITH

# View traces at https://smith.langchain.com/
```

## Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yonca-langgraph
spec:
  replicas: 3
  selector:
    matchLabels:
      app: yonca-langgraph
  template:
    metadata:
      labels:
        app: yonca-langgraph
    spec:
      containers:
      - name: langgraph
        image: yonca-langgraph:latest
        ports:
        - containerPort: 2024
        env:
        - name: PYTHONPATH
          value: /app/src
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: yonca-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: yonca-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 2024
          initialDelaySeconds: 40
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 2024
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: yonca-langgraph
spec:
  selector:
    app: yonca-langgraph
  ports:
  - port: 2024
    targetPort: 2024
  type: ClusterIP
```

### Cloud Run (GCP)

```bash
# Build and push
docker build -f Dockerfile.langgraph -t gcr.io/your-project/yonca-langgraph:latest .
docker push gcr.io/your-project/yonca-langgraph:latest

# Deploy
gcloud run deploy yonca-langgraph \
  --image gcr.io/your-project/yonca-langgraph:latest \
  --port 2024 \
  --set-env-vars PYTHONPATH=/app/src,DATABASE_URL=$DATABASE_URL \
  --allow-unauthenticated
```

## Summary

✅ **Dockerfile** created with proper PYTHONPATH setup
✅ **docker-compose** service added with profile support
✅ **Health checks** implemented for reliability
✅ **Hot reload** enabled via volume mounts
✅ **Networking** configured for internal communication
✅ **Documentation** covers all deployment scenarios

## Next Steps

1. ✅ Docker deployment complete
2. ⏳ Add integration tests
3. ⏳ Add health check endpoints
4. ⏳ Add performance monitoring

## References

- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)
- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [LangGraph Dev Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/)
