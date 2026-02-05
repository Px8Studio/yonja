# Dockerfile for ZekaLab MCP Server
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY src/alim/mcp_server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port
EXPOSE 7777

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7777/health || exit 1

# ────────────────────────────────────────────────────────────────────────────
# DEVELOPMENT: Hot reload enabled
# ────────────────────────────────────────────────────────────────────────────
FROM base AS development
# Code mounted via volume, hot reload enabled
CMD ["python", "-m", "uvicorn", "alim.mcp_server.main:app", "--host", "0.0.0.0", "--port", "7777", "--reload", "--reload-dir", "/app/src"]

# ────────────────────────────────────────────────────────────────────────────
# PRODUCTION: No hot reload, code baked in
# ────────────────────────────────────────────────────────────────────────────
FROM base AS production
# Copy application code
COPY src/ /app/src/
CMD ["python", "-m", "uvicorn", "alim.mcp_server.main:app", "--host", "0.0.0.0", "--port", "7777"]
