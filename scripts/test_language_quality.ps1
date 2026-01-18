# Test script for language quality validation
# Tests both Groq (cloud) and Ollama (local) providers for Turkish leakage

param(
    [Parameter(Mandatory=$false)]
    [string]$Provider = "both",  # "groq", "ollama", or "both"
    
    [Parameter(Mandatory=$false)]
    [string]$GroqApiKey = $env:YONCA_GROQ_API_KEY
)

# Test cases with expected Azerbaijani words
$testCases = @(
    @{
        Question = "Buğda əkmək üçün ən yaxşı vaxt nədir?"
        ExpectedWords = @("Sentyabr", "Oktyabr", "torpaq")
        ForbiddenWords = @("Eylül", "ekim", "zemin", "sulama")
        Description = "Basic wheat planting question (tests months and soil)"
    },
    @{
        Question = "Pomidor üçün suvarma cədvəli düzəlt"
        ExpectedWords = @("suvarma", "torpaq", "bitki")
        ForbiddenWords = @("sulama", "zemin", "tohum", "ürün")
        Description = "Irrigation schedule (tests agricultural terms)"
    },
    @{
        Question = "Sentyabr ayında hansı məhsulları əkmək olar?"
        ExpectedWords = @("Sentyabr", "məhsul", "əkin", "torpaq")
        ForbiddenWords = @("Eylül", "ürün", "ekim", "zemin")
        Description = "September planting (tests month name preservation)"
    }
)

# Load enhanced system prompt
$projectRoot = Split-Path -Parent $PSScriptRoot
$promptPath = Join-Path $projectRoot "prompts\system\master_v1.0.0_az_strict.txt"

if (-not (Test-Path $promptPath)) {
    Write-Host "❌ Enhanced system prompt not found at: $promptPath" -ForegroundColor Red
    Write-Host "Creating fallback prompt..." -ForegroundColor Yellow
    $systemPrompt = "Sən Yonca AI - Azərbaycan fermerlərinin süni intellekt köməkçisisən. Yalnız Azərbaycan dilində danış."
} else {
    $systemPrompt = Get-Content $promptPath -Raw -Encoding UTF8
    Write-Host "✅ Loaded enhanced system prompt" -ForegroundColor Green
}

# Function to test Groq
function Test-GroqProvider {
    param($TestCase)
    
    if (-not $GroqApiKey) {
        Write-Host "⚠️  Groq API key not found. Set YONCA_GROQ_API_KEY environment variable." -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "`n🌩️  Testing Groq (llama-3.3-70b-versatile)..." -ForegroundColor Cyan
    Write-Host "Question: $($TestCase.Question)" -ForegroundColor White
    
    $headers = @{ 
        "Authorization" = "Bearer $GroqApiKey"
        "Content-Type" = "application/json" 
    }
    
    $body = @{
        model = "llama-3.3-70b-versatile"
        messages = @(
            @{
                role = "system"
                content = $systemPrompt
            },
            @{
                role = "user"
                content = $TestCase.Question
            }
        )
        temperature = 0.7
        max_tokens = 500
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod `
            -Uri "https://api.groq.com/openai/v1/chat/completions" `
            -Method Post `
            -Headers $headers `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec 30
        
        $answer = $response.choices[0].message.content
        
        return @{
            Provider = "Groq"
            Model = "llama-3.3-70b-versatile"
            Answer = $answer
            TokensUsed = $response.usage.total_tokens
        }
    } catch {
        Write-Host "❌ Groq API error: $_" -ForegroundColor Red
        return $null
    }
}

# Function to test Ollama
function Test-OllamaProvider {
    param($TestCase)
    
    Write-Host "`n🏠 Testing Ollama (atllama)..." -ForegroundColor Cyan
    Write-Host "Question: $($TestCase.Question)" -ForegroundColor White
    
    $headers = @{ 
        "Content-Type" = "application/json" 
    }
    
    $body = @{
        model = "atllama"
        messages = @(
            @{
                role = "system"
                content = $systemPrompt
            },
            @{
                role = "user"
                content = $TestCase.Question
            }
        )
        stream = $false
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:11434/api/chat" `
            -Method Post `
            -Headers $headers `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
            -TimeoutSec 120
        
        return @{
            Provider = "Ollama"
            Model = "atllama"
            Answer = $response.message.content
            TokensUsed = "N/A"
        }
    } catch {
        Write-Host "❌ Ollama error: $_" -ForegroundColor Red
        Write-Host "   Make sure Ollama is running and atllama model is installed." -ForegroundColor Yellow
        return $null
    }
}

# Function to validate response
function Test-LanguageQuality {
    param($Response, $TestCase)
    
    if (-not $Response) {
        return @{
            Passed = $false
            Score = 0
            Issues = @("No response received")
        }
    }
    
    $answer = $Response.Answer
    $issues = @()
    $score = 100
    
    # Check for forbidden Turkish words
    foreach ($forbidden in $TestCase.ForbiddenWords) {
        if ($answer -match $forbidden) {
            $issues += "❌ Found Turkish word: '$forbidden'"
            $score -= 25
        }
    }
    
    # Check for expected Azerbaijani words
    $foundExpected = 0
    foreach ($expected in $TestCase.ExpectedWords) {
        if ($answer -match $expected) {
            $foundExpected++
        }
    }
    
    if ($foundExpected -eq 0) {
        $issues += "⚠️  None of the expected Azerbaijani words found"
        $score -= 10
    }
    
    # Overall assessment
    $passed = $issues.Count -eq 0
    
    return @{
        Passed = $passed
        Score = [Math]::Max(0, $score)
        Issues = $issues
        FoundExpectedWords = $foundExpected
        TotalExpectedWords = $TestCase.ExpectedWords.Count
    }
}

# Main execution
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  Yonca AI - Language Quality Test Suite" -ForegroundColor Magenta
Write-Host "  Testing for Turkish Language Leakage" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta

$results = @()

foreach ($testCase in $testCases) {
    Write-Host "`n─────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "📋 Test: $($testCase.Description)" -ForegroundColor White
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor Gray
    
    # Test Groq
    if ($Provider -in @("groq", "both")) {
        $groqResponse = Test-GroqProvider -TestCase $testCase
        if ($groqResponse) {
            Write-Host "`n📄 Response:" -ForegroundColor Gray
            Write-Host $groqResponse.Answer -ForegroundColor White
            Write-Host "`n🔍 Validation:" -ForegroundColor Gray
            
            $validation = Test-LanguageQuality -Response $groqResponse -TestCase $testCase
            
            if ($validation.Passed) {
                Write-Host "✅ PASSED - Score: $($validation.Score)/100" -ForegroundColor Green
            } else {
                Write-Host "❌ FAILED - Score: $($validation.Score)/100" -ForegroundColor Red
                foreach ($issue in $validation.Issues) {
                    Write-Host "   $issue" -ForegroundColor Yellow
                }
            }
            
            $results += @{
                Test = $testCase.Description
                Provider = "Groq"
                Passed = $validation.Passed
                Score = $validation.Score
            }
        }
    }
    
    # Test Ollama
    if ($Provider -in @("ollama", "both")) {
        $ollamaResponse = Test-OllamaProvider -TestCase $testCase
        if ($ollamaResponse) {
            Write-Host "`n📄 Response:" -ForegroundColor Gray
            Write-Host $ollamaResponse.Answer -ForegroundColor White
            Write-Host "`n🔍 Validation:" -ForegroundColor Gray
            
            $validation = Test-LanguageQuality -Response $ollamaResponse -TestCase $testCase
            
            if ($validation.Passed) {
                Write-Host "✅ PASSED - Score: $($validation.Score)/100" -ForegroundColor Green
            } else {
                Write-Host "❌ FAILED - Score: $($validation.Score)/100" -ForegroundColor Red
                foreach ($issue in $validation.Issues) {
                    Write-Host "   $issue" -ForegroundColor Yellow
                }
            }
            
            $results += @{
                Test = $testCase.Description
                Provider = "Ollama"
                Passed = $validation.Passed
                Score = $validation.Score
            }
        }
    }
}

# Summary
Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  Test Summary" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta

$groqResults = $results | Where-Object { $_.Provider -eq "Groq" }
$ollamaResults = $results | Where-Object { $_.Provider -eq "Ollama" }

if ($groqResults) {
    $groqPassed = ($groqResults | Where-Object { $_.Passed }).Count
    $groqTotal = $groqResults.Count
    $groqAvgScore = ($groqResults | Measure-Object -Property Score -Average).Average
    
    Write-Host "`n🌩️  Groq (llama-3.3-70b-versatile):" -ForegroundColor Cyan
    Write-Host "   Tests Passed: $groqPassed / $groqTotal" -ForegroundColor White
    Write-Host "   Average Score: $([Math]::Round($groqAvgScore, 1))/100" -ForegroundColor White
}

if ($ollamaResults) {
    $ollamaPassed = ($ollamaResults | Where-Object { $_.Passed }).Count
    $ollamaTotal = $ollamaResults.Count
    $ollamaAvgScore = ($ollamaResults | Measure-Object -Property Score -Average).Average
    
    Write-Host "`n🏠 Ollama (atllama):" -ForegroundColor Cyan
    Write-Host "   Tests Passed: $ollamaPassed / $ollamaTotal" -ForegroundColor White
    Write-Host "   Average Score: $([Math]::Round($ollamaAvgScore, 1))/100" -ForegroundColor White
}

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "✅ Testing complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review any failed tests above" -ForegroundColor White
Write-Host "2. If Turkish words found, adjust system prompt" -ForegroundColor White
Write-Host "3. Consider using dual-model strategy (Qwen→Llama)" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════`n" -ForegroundColor Magenta
