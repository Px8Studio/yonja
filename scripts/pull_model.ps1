# PowerShell script to pull Ollama model for local development

Write-Host "🔍 Checking if Ollama container is running..." -ForegroundColor Cyan

$ollamaRunning = docker ps --format "{{.Names}}" | Select-String -Pattern "alim-ollama"

if (-not $ollamaRunning) {
    Write-Host "❌ Ollama container is not running." -ForegroundColor Red
    Write-Host "Please start the Docker stack first:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.local.yml up -d" -ForegroundColor White
    exit 1
}

Write-Host "✅ Ollama container is running" -ForegroundColor Green

Write-Host "📥 Pulling Ollama model: qwen3:4b" -ForegroundColor Cyan
Write-Host "This may take a few minutes depending on your internet connection..." -ForegroundColor Yellow

docker exec -it alim-ollama ollama pull qwen3:4b

Write-Host ""
Write-Host "✅ Model pulled successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now test the model:" -ForegroundColor Cyan
Write-Host "  docker exec -it alim-ollama ollama run qwen3:4b" -ForegroundColor White
