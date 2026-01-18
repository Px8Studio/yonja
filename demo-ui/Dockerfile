# Demo UI Dockerfile
# Builds the Chainlit demo interface for Yonca AI

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/demo-ui

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Dependencies Stage
# ============================================
FROM base as deps

# Copy requirements files
COPY demo-ui/requirements.txt demo-ui/requirements.txt
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r demo-ui/requirements.txt

# ============================================
# Production Stage
# ============================================
FROM deps as production

# Copy application code
COPY src/ /app/src/
COPY demo-ui/ /app/demo-ui/
COPY prompts/ /app/prompts/

# Create data directory
RUN mkdir -p /app/data

# Set working directory to demo-ui
WORKDIR /app/demo-ui

# Expose Chainlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# Run Chainlit
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8501"]

# ============================================
# Development Stage
# ============================================
FROM deps as development

# Install development dependencies
RUN pip install --no-cache-dir \
    watchfiles \
    pytest \
    pytest-asyncio

# Copy application code
COPY src/ /app/src/
COPY demo-ui/ /app/demo-ui/
COPY prompts/ /app/prompts/

# Create data directory
RUN mkdir -p /app/data

# Set working directory to demo-ui
WORKDIR /app/demo-ui

# Expose Chainlit port
EXPOSE 8501

# Run Chainlit with hot reload
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8501", "-w"]
