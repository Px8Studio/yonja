# Multi-stage build for ALİM

# ============================================
# Stage 1: Base
# ============================================
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Stage 2: Development
# ============================================
FROM base AS development

# Copy project files needed for installation
COPY pyproject.toml README.md ./
COPY requirements.txt .
COPY src/ ./src/
COPY prompts/ ./prompts/

# Install dependencies
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "alim.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 3: Production
# ============================================
FROM base AS production

# Create non-root user
RUN useradd -m -u 1000 alim

# Copy project files needed for installation
COPY pyproject.toml README.md ./
COPY requirements.txt .
COPY --chown=alim:alim src/ ./src/
COPY --chown=alim:alim prompts/ ./prompts/

# Install production dependencies only
RUN pip install --no-cache-dir -r requirements.txt

USER alim

ENV PYTHONPATH=/app/src

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "alim.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
