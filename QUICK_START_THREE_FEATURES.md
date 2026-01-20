# 🚀 Quick Start: Three New Features

## 1️⃣ NL-to-SQL (Natural Language to SQL)

**Ask in chat:**
```
Sahəsi 50 hektardan çox olan fermləri göstər
```

**What happens:**
1. Supervisor detects `DATA_QUERY` intent
2. Routes to `nl_to_sql` node
3. Maverick generates: `SELECT * FROM farms WHERE total_area_ha > 50;`
4. `sql_executor` runs query against Yonca App DB
5. Results formatted as markdown table

**Environment:**
```bash
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
```

---

## 2️⃣ Vision-to-Action (Image Analysis)

**In Chainlit demo UI:**
1. Click 📸 **Upload Image** button
2. Select crop photo (JPG/PNG)
3. Type: `Bu zərərveridirmi?` or similar
4. Submit

**What happens:**
1. Chainlit saves image to temp location
2. Supervisor detects `VISION_ANALYSIS` intent
3. Routes to `vision_to_action` node
4. Maverick analyzes and returns action plan:
   ```
   Müşahidə: Pomidor bitkilərində qırmızı ləkələr
   Risk: Septoria xəstəliyi
   Tövsiyə: Fungisid tətbiq et, suvarmanı azalt
   Xəbərdarlıq: HIGH
   ```

**Multimodal support:** Currently text-based with image path logging. Ready for true multimodal when vLLM adds native image endpoints.

---

## 3️⃣ FastAPI Vision Endpoint

**For mobile apps / external systems:**

```bash
# Upload image
curl -X POST \
  -F "files=@photo.jpg" \
  -F "message=Bu zərərveridirmi?" \
  -F "user_id=farmer_123" \
  http://localhost:8000/api/vision/analyze

# Response
{
  "status": "ok",
  "response": "Müşahidə: Pest tapılmadı. Müvafiq haldir.",
  "thread_id": "vision_abc123"
}
```

**Features:**
- Multiple file support
- Async processing
- Langfuse tracing (see traces at http://localhost:3001)
- Temp file auto-cleanup

---

## 🎯 Node Flow Diagram

```
┌─ NL-to-SQL Query Flow ─────────────────┐
│  User: "Hansı fermlər suvarılmadı?"     │
│         ↓ (DATA_QUERY intent)           │
│     nl_to_sql node                      │
│         ↓                               │
│  Generated: SELECT * FROM parcels ...   │
│         ↓                               │
│     sql_executor node                   │
│         ↓                               │
│  Results: [Markdown table]              │
└────────────────────────────────────────┘

┌─ Vision Analysis Flow ─────────────────┐
│  User: [uploads photo] + "Zərərverici?" │
│         ↓ (VISION_ANALYSIS intent)      │
│     vision_to_action node               │
│         ↓                               │
│  Multimodal message (text + image)      │
│         ↓                               │
│  Maverick LLM analyzes                  │
│         ↓                               │
│  Response: "Müşahidə: Zərərverici X"    │
└────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Environment

```bash
# LLM Provider (required)
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_API_KEY=gsk_your_key_here
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct

# Database (for SQL queries)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/yonca

# Langfuse (for tracing)
YONCA_LANGFUSE_SECRET_KEY=...
YONCA_LANGFUSE_PUBLIC_KEY=...
YONCA_LANGFUSE_HOST=http://localhost:3001

# Optional: Image upload size limit
YONCA_MAX_IMAGE_SIZE_MB=10
```

### Docker Compose

```bash
# Ensure services are running
docker-compose -f docker-compose.local.yml up -d postgres redis langfuse ollama

# Check status
docker-compose -f docker-compose.local.yml ps
```

---

## 🧪 Test Commands

### Test NL-to-SQL Locally

```bash
python3 << 'EOF'
import asyncio
from yonca.agent.nodes.nl_to_sql import nl_to_sql_node
from yonca.agent.state import UserIntent

async def test():
    state = {
        'current_input': 'Pambıq əkin sahəsi 100 hektardan çox olan fermləri göstər',
        'nodes_visited': [],
        'messages': [],
    }
    result = await nl_to_sql_node(state)
    print("Generated SQL:")
    print(result['current_response'])

asyncio.run(test())
EOF
```

### Test Vision Analysis Locally

```bash
python3 << 'EOF'
import asyncio
from yonca.agent.nodes.vision_to_action import vision_to_action_node

async def test():
    state = {
        'current_input': 'Bu şəkildə pomidor bitkilərində qara ləkələr var. Nə zərərveridirdir?',
        'nodes_visited': [],
        'messages': [],
    }
    result = await vision_to_action_node(state)
    print("Analysis:")
    print(result['current_response'])

asyncio.run(test())
EOF
```

### Full Feature Demo

```bash
python scripts/demo_three_features.py
```

---

## 📊 Langfuse Tracing

Every request is automatically traced with metadata:

```json
{
  "alem": {
    "version": "0.1.0",
    "updated_at": "2026-01-20T..."
  },
  "models": {
    "nl_to_sql": {
      "id": "meta-llama/llama-4-maverick-17b-128e-instruct",
      "fingerprint": "..."
    }
  },
  "uploaded_images": 2,
  "farm_id": "farm_001",
  "expertise_areas": ["pambiq", "gubre"]
}
```

**View traces:** http://localhost:3001/traces

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "SQL: table not found" | Verify table names in DB schema; check database connection |
| "Image upload failed" | Check file format (PNG/JPEG); file size < 10MB |
| "NL-to-SQL generates invalid SQL" | Add more examples to prompt; try different phrasing |
| "Vision analysis slow" | Normal (Maverick ~200 tok/s); check GPU/CPU resource |
| "Langfuse traces not appearing" | Verify API keys; check network connectivity to localhost:3001 |

---

## 📚 Full Documentation

- [16-ADVANCED-FEATURES.md](docs/zekalab/16-ADVANCED-FEATURES.md) — Comprehensive guide with architecture diagrams
- [12-DEPLOYMENT-PRICING.md](docs/zekalab/12-DEPLOYMENT-PRICING.md) — Deployment options (includes fixed mermaid diagram)

---

## 🎉 Ready to Go!

```bash
# 1. Start all services
cd dev
task "🌿 Yonca AI: 🚀 Start All"

# 2. Start demo UI
cd demo-ui
chainlit run app.py -w --port 8501

# 3. Try it out
# - Open http://localhost:8501
# - Upload an image or type a SQL query
# - Watch Langfuse traces at http://localhost:3001
```

---

**Questions?** Check [SESSION_SUMMARY.md](SESSION_SUMMARY.md) or [16-ADVANCED-FEATURES.md](docs/zekalab/16-ADVANCED-FEATURES.md)
