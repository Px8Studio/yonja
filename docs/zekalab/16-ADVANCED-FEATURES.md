# 🎨 Advanced Features: Multimodal, SQL, Vision

## Overview

Three powerful nodes extend ALEM's capabilities beyond text:

1. **Multimodal Images** — Attach images to messages for analysis
2. **NL-to-SQL** — Convert questions into structured database queries
3. **Vision-to-Action** — Analyze crop photos and propose interventions
4. **SQL Executor** — Execute generated queries and return tabular results

---

## 1. Multimodal Image Support

**What it does:** Converts image file paths to base64-encoded content and attaches them to LangChain messages.

**Usage:**

```python
from yonca.llm.multimodal import create_multimodal_message

msg = create_multimodal_message(
    text="This crop looks diseased. What pest is it?",
    image_paths=["/path/to/photo.jpg", "/path/to/photo2.png"]
)
# Returns: HumanMessage with images as base64 data URLs
```

**Supported formats:** PNG, JPEG, GIF, WebP

**Flow:**
```
User uploads image
       ↓
Chainlit UI hook (`on_file_upload`)
       ↓
Saved to temp directory
       ↓
Path passed to LangGraph state
       ↓
`create_multimodal_message()` converts to base64
       ↓
`vision_to_action_node` processes with LLM
```

---

## 2. NL-to-SQL Node

**What it does:** Generates PostgreSQL queries from natural language questions.

**Node:** `src/yonca/agent/nodes/nl_to_sql.py`

**Trigger:** User message containing keywords like "sql", "query", "parcel", "farm"

**Example:**

```
Input:  "Show me farms with area > 50 hectares"
↓
Output: SELECT * FROM farms WHERE total_area_ha > 50;
```

**Configuration:**
- Model: Llama 4 Maverick (default) or Qwen3 (legacy)
- Temperature: 0.0 (deterministic)
- Max tokens: 300

**Limitations:**
- No DELETE/UPDATE/DROP — read-only enforced
- Table names must match Yonca App DB schema
- Complex joins left to user refinement

---

## 3. Vision-to-Action Node

**What it does:** Analyzes uploaded crop photos and proposes farmer-facing action plans.

**Node:** `src/yonca/agent/nodes/vision_to_action.py`

**Trigger:** User message containing keywords like "photo", "image", "şəkil"

**Example:**

```
Input:  "şəkil analiz et" + [uploaded_image.jpg]
↓
Output: 
Müşahidə: Pomidor bitkilərində sarı ləkələr
Risk: Septoria xəstəliyi
Tövsiyə: Fungisid tətbiq et, suvarmanı azalt
Xəbərdarlıq: HIGH
```

**Current status:** Text-based (image paths logged to Langfuse); ready for true multimodal models

---

## 4. SQL Executor Node

**What it does:** Executes NL-generated SQL against Yonca App DB and formats results as markdown tables.

**Node:** `src/yonca/agent/nodes/sql_executor.py`

**Flow:**
```
nl_to_sql node generates SQL
       ↓
sql_executor receives in state.current_response
       ↓
Connects to PostgreSQL via `get_db_session()`
       ↓
Executes (read-only enforced)
       ↓
Formats result as markdown table
       ↓
Returns to farmer in chat
```

**Safety:**
- Only SELECT statements allowed (regex check)
- Database session timeout: 30 seconds
- Max result rows: 1000 (configurable)

---

## 5. FastAPI Vision Endpoint

**What it does:** HTTP endpoint for uploading images and triggering vision analysis from mobile/external apps.

**Route:** `POST /api/vision/analyze`

**Code:** `src/yonca/api/routes/vision.py`

**Example:**

```bash
curl -X POST \
  -F "files=@photo.jpg" \
  -F "message=Bu zərərveridirmi?" \
  -F "user_id=user_123" \
  -F "thread_id=thread_456" \
  http://localhost:8000/api/vision/analyze
```

**Response:**
```json
{
  "status": "ok",
  "response": "Müşahidə: Pest tapılmadı. Müvafiq haldir.",
  "thread_id": "thread_456"
}
```

**Features:**
- Multiple file upload support
- Automatic temp file cleanup
- Langfuse integration (traces all calls)
- User + thread tracking

---

## Integration in Chainlit Demo UI

### Upload Hook

```python
@cl.on_event("upload")
async def on_file_upload(files: list[cl.UploadedFile]):
    # Saves files to session
    cl.user_session.set("uploaded_images", [saved_path1, saved_path2])
```

### On Message

```python
uploaded_images = cl.user_session.get("uploaded_images", [])
langfuse_handler = create_langfuse_handler(
    metadata={"uploaded_images": uploaded_images}
)
```

### Use Case:
1. User clicks **📸 Upload Image** button in chat
2. Chainlit saves to temp location
3. User types: "Bu nə zərərveridirdir?"
4. Message + image path flows to `vision_to_action`
5. LLM analyzes and returns action plan
6. Langfuse logs image count for analytics

---

## Graph Flow Diagram

```
START
  │
  ▼
supervisor
  │
  ├─→ nl_to_sql ──→ sql_executor ──→ validator ──→ END
  │
  ├─→ vision_to_action ──────────→ validator ──→ END
  │
  └─→ agronomist / weather / ... ──→ validator ──→ END
```

---

## Configuration

### Environment Variables

```bash
# Multimodal image max size
YONCA_MAX_IMAGE_SIZE_MB=10

# SQL executor timeout
YONCA_SQL_EXECUTOR_TIMEOUT_SEC=30

# Vision model (same as active LLM provider)
YONCA_LLM_PROVIDER=groq
YONCA_GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
```

### Model Selection

- **Multimodal images:** Llama 4 Maverick (native multimodal)
- **NL-to-SQL:** Qwen 3 (best structured output) or Maverick
- **Vision analysis:** Maverick (best language quality)

---

## Testing

### Unit Tests

```bash
# Test NL-to-SQL
pytest tests/unit/test_nl_to_sql.py -v

# Test multimodal messages
pytest tests/unit/test_multimodal.py -v

# Test SQL executor
pytest tests/unit/test_sql_executor.py -v
```

### Integration Test

```bash
python scripts/demo_three_features.py
```

---

## Future Enhancements

1. **True Multimodal** — Stream image tokens directly to Llama 4 Maverick (when vLLM supports native image endpoints)
2. **SQL Optimization** — Auto-explain slow queries and suggest indexes
3. **Image Crop Detection** — YOLO-based bounding boxes for pest hotspots
4. **Batch Processing** — Queue images for async analysis
5. **Export Results** — Generate PDF reports with charts from SQL results

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Image format not supported" | Ensure PNG/JPEG; check file size < 10MB |
| "SQL parse error" | Verify table names match DB schema; test with SELECT * LIMIT 1 |
| "No multimodal support" | Update to Llama 4 Maverick model; check provider config |
| "Langfuse not logging images" | Verify `uploaded_images` in metadata; check API keys |
