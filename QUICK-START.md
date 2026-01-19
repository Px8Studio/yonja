# Quick Start: Testing the Language Improvements

## ⚡ 5-Minute Quick Test

### Option 1: Test with Groq (Recommended - Fastest)

1. **Set your Groq API key**:
   ```powershell
   # Get free key at: https://console.groq.com/
   $env:YONCA_GROQ_API_KEY = "gsk_your_key_here"
   $env:YONCA_LLM_PROVIDER = "groq"
   $env:YONCA_GROQ_MODEL = "llama-3.3-70b-versatile"
   ```

2. **Run the test script**:
   ```powershell
   cd C:\Users\rjjaf\_Projects\yonja
   .\scripts\test_language_quality.ps1 -Provider groq
   ```

3. **Check results**:
   - ✅ Look for: "Sentyabr", "torpaq", "suvarma"
   - ❌ Should NOT see: "Eylül", "zemin", "sulama"

### Option 2: Test with Ollama (Local - Slower but Free)

1. **Make sure Ollama is running**:
   ```powershell
   # Check if atllama model is available
   docker exec yonca-ollama ollama list
   ```

2. **If atllama not found, import it**:
   ```powershell
   # Run the model setup task
   # This will import ATLLaMA from models/atllama.v3.5.Q4_K_M.gguf
   ```

3. **Run the test**:
   ```powershell
   .\scripts\test_language_quality.ps1 -Provider ollama
   ```

---

## 🧪 Manual API Test

### Using PowerShell (Direct Groq Test)

```powershell
# Load the enhanced system prompt
$systemPrompt = Get-Content "prompts\system\master_v1.0.0_az_strict.txt" -Raw -Encoding UTF8

# Call Groq API
$headers = @{ 
    "Authorization" = "Bearer $env:YONCA_GROQ_API_KEY"
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
            content = "Buğda əkmək üçün ən yaxşı vaxt nədir?"
        }
    )
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod `
    -Uri "https://api.groq.com/openai/v1/chat/completions" `
    -Method Post `
    -Headers $headers `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($body))

Write-Host $response.choices[0].message.content
```

### Expected Good Response:
```
📋 **Qısa Cavab**: Buğda əkini üçün ən yaxşı vaxt Sentyabr və Oktyabr 
aylarıdır. Bu dövr torpaq rütubəti və hava şəraiti üçün idealdır.

📝 **Ətraflı İzah**: Azərbaycanda buğda əkini əsasən payız mövsümündə 
aparılır. Sentyabr ayının sonu və Oktyabr ayının əvvəli ən optimal 
vaxtdır, çünki:

✅ **Tövsiyə Olunan Addımlar**:
1. Torpağı Avqust sonu - Sentyabr əvvəlində hazırlayın
2. Toxumları Sentyabr 20 - Oktyabr 15 arasında əkin
3. Suvarma sistemini yoxlayın
...
```

### Bad Response (Turkish leakage):
```
Buğday ekimi için en iyi zaman Eylül ayıdır. Zemin hazırlığı...
❌ "Eylül" - should be "Sentyabr"
❌ "zemin" - should be "torpaq"
```

---

## 🚀 Production Deployment

### 1. Update .env file
```bash
# Production config
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_API_KEY=gsk_your_production_key
YONCA_GROQ_MODEL=llama-3.3-70b-versatile

# Fallback to local if Groq unavailable
YONCA_OLLAMA_MODEL=atllama
YONCA_OLLAMA_BASE_URL=http://localhost:11434
```

### 2. Restart API server
```powershell
# Stop existing server (Ctrl+C if running)

# Start with new config
cd C:\Users\rjjaf\_Projects\yonja
.\.venv\Scripts\python.exe -m uvicorn yonca.api.main:app --reload
```

### 3. Test via API
```powershell
# Test endpoint
$body = @{
    message = "Buğda əkmək üçün ən yaxşı vaxt nədir?"
    language = "az"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 📊 What to Look For

### Quality Indicators

**✅ Good Azerbaijani Response:**
- Uses "Sentyabr", "Oktyabr", "Noyabr", "Dekabr" for months
- Uses "torpaq" for soil
- Uses "suvarma" for irrigation
- Uses "məhsul" for crop/product
- Uses "toxum" for seed
- Uses "əkin" for planting/sowing

**❌ Turkish Leakage Signs:**
- "Eylül" instead of "Sentyabr"
- "zemin" instead of "torpaq"
- "sulama" instead of "suvarma"
- "ürün" instead of "məhsul"
- "tohum" instead of "toxum"
- "ekim" instead of "əkin"

---

## 🔧 Troubleshooting

### Issue: Groq API Error
```
❌ Groq API error: 401 Unauthorized
```

**Solution**: Check API key
```powershell
# Verify key is set
$env:YONCA_GROQ_API_KEY
# Should output: gsk_...

# If empty, set it:
$env:YONCA_GROQ_API_KEY = "gsk_your_key_here"
```

### Issue: Ollama Not Running
```
❌ Ollama error: No connection could be made
```

**Solution**: Start Ollama
```powershell
# Check Docker containers
docker ps | Select-String "ollama"

# If not running, start services
docker-compose -f docker-compose.local.yml up -d ollama
```

### Issue: atllama Model Not Found
```
❌ model 'atllama' not found
```

**Solution**: Import the model
```powershell
# Check available models
docker exec yonca-ollama ollama list

# If atllama not listed, import it
docker exec yonca-ollama ollama create atllama -f /models/atllama.v3.5.Q4_K_M.gguf
```

---

## 📈 Performance Expectations

### Groq (Cloud)
- **Speed**: 2-3 seconds for 500-token response
- **Cost**: Free tier (rate limits apply)
- **Quality**: High Azerbaijani quality, minimal Turkish leakage

### Ollama + atllama (Local)
- **Speed**: 30-60 seconds on CPU, 5-10 seconds on GPU
- **Cost**: Free (uses local hardware)
- **Quality**: Best Azerbaijani quality, zero Turkish leakage

---

## ✅ Success Criteria

You'll know it's working when:

1. ✅ Test script shows 100% pass rate
2. ✅ No Turkish words in responses
3. ✅ Month names are Russian-origin (Sentyabr, etc.)
4. ✅ Responses are helpful and contextually appropriate
5. ✅ Farmers can understand and trust the advice

---

## 🎯 Next Steps After Testing

1. **If tests pass**: Deploy to production
2. **If tests fail**: 
   - Check which words are leaking
   - Adjust system prompt in `prompts/system/master_v1.0.0_az_strict.txt`
   - Add more forbidden words to negative constraints
   - Re-run tests

3. **For LangGraph integration**:
   - Use `get_model_for_node()` from `model_roles.py`
   - Route calculations to Qwen
   - Route responses to Llama/ATLLaMA

---

## 📚 Documentation Reference

- **Full Guide**: [LANGUAGE-INTERFERENCE-GUIDE.md](../docs/zekalab/LANGUAGE-INTERFERENCE-GUIDE.md)
- **Quick Ref**: [MODEL-SELECTION-QUICK-REF.md](../docs/zekalab/MODEL-SELECTION-QUICK-REF.md)
- **Implementation**: [IMPLEMENTATION-SUMMARY.md](../docs/zekalab/IMPLEMENTATION-SUMMARY.md)
- **System Prompts**: [prompts/system/](../prompts/system/)
- **Model Config**: [src/yonca/llm/model_roles.py](../src/yonca/llm/model_roles.py)

---

**Ready to test?** Run: `.\scripts\test_language_quality.ps1`
