# Dockerfile for ZekaLab MCP Server
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY src/yonca/mcp_server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7777/health')" || exit 1

# Expose port
EXPOSE 7777

# Run server
CMD ["python", "-m", "uvicorn", "yonca.mcp_server.main:app", "--host", "0.0.0.0", "--port", "7777"]
