#!/bin/bash
# Script to pull Ollama model for local development

set -e

echo "🔍 Checking if Ollama container is running..."

if ! docker ps | grep -q yonca-ollama; then
    echo "❌ Ollama container is not running."
    echo "Please start the Docker stack first:"
    echo "  docker-compose -f docker-compose.local.yml up -d"
    exit 1
fi

echo "✅ Ollama container is running"

echo "📥 Pulling Ollama model: qwen3:4b"
echo "This may take a few minutes depending on your internet connection..."

docker exec -it yonca-ollama ollama pull qwen3:4b

echo ""
echo "✅ Model pulled successfully!"
echo ""
echo "You can now test the model:"
echo "  docker exec -it yonca-ollama ollama run qwen3:4b"
