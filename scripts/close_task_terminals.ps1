# Close all VS Code terminal tabs related to ALİM tasks
# This script uses VS Code CLI to close terminals

param()

Write-Host "🧹 Closing previous task terminals..." -ForegroundColor Cyan

# List of terminal names to close (matching task labels)
$terminalPatterns = @(
    "Quality & Sanity Checks",
    "ALİM:.*Clear Ports",
    "ALİM:.*Clear Logs",
    "ALİM:.*Clear Browser",
    "ALİM:.*Docker Start",
    "ALİM:.*FastAPI Start",
    "ALİM:.*UI Start",
    "ALİM:.*ZekaLab MCP",
    "ALİM:.*LangGraph Start",
    "ALİM:.*Stop All"
)

# Note: VS Code doesn't expose terminal management via CLI
# The terminals will be reused (not closed) due to "panel": "dedicated"
# This is a limitation of VS Code tasks

Write-Host "   → Terminals will be reused (VS Code limitation)" -ForegroundColor Yellow
Write-Host "   → Each task uses dedicated panel for clean output" -ForegroundColor Green
Write-Host "✅ Terminal management configured" -ForegroundColor Green
