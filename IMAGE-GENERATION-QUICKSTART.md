# 🎨 Image Generation Quick Reference

## 🚀 Quick Start

### 1. Setup (One-Time)

```bash
# Option A: Use Ollama (Local - Recommended for Privacy)
docker run --gpus=all -d -v ollama_data:/root/.ollama \
  -p 11434:11434 --name ollama ollama/ollama

docker exec ollama ollama pull stable-diffusion-v1-5

# Option B: Use Groq (Cloud - Fast & Cheap)
export GROQ_API_KEY=gsk_... # Get from console.groq.com

# Option C: Use Hugging Face (Cloud - Free)
export HUGGINGFACE_API_KEY=hf_... # Get from huggingface.co/settings/tokens

# Option D: Use OpenAI (Cloud - Premium)
export OPENAI_API_KEY=sk-... # Get from platform.openai.com
```

### 2. Usage (In Chat)

```
/image A beautiful farm landscape at sunrise
/img Crops growing in a field
/image                          # Show help
```

### 3. Result

```
✨ Image Generated via 🏠 Local (Ollama)
"A beautiful farm landscape at sunrise"
[Image displayed in chat]
```

## 📊 Provider Comparison

| Provider | Speed | Cost | Quality | Setup |
|----------|-------|------|---------|-------|
| Ollama | ⚡⚡⚡ | Free | ⭐⭐⭐ | Docker |
| Groq | ⚡⚡ | $ | ⭐⭐⭐⭐ | API Key |
| HF | ⚡ | Free | ⭐⭐⭐⭐ | API Key |
| OpenAI | ⚡⚡ | $$ | ⭐⭐⭐⭐⭐ | API Key |

## 💡 Tips

- **Best for Privacy**: Use Ollama (local, GPU needed)
- **Best for Speed**: Use Groq (cloud, fast)
- **Best for Free**: Use Hugging Face (cloud, free tier)
- **Best for Quality**: Use OpenAI (cloud, premium)
- **System Auto-tries**: Ollama → Groq → HF → OpenAI

## 🎯 Quality Presets

```
/image Description           # STANDARD (512x512, ~15s)
/image-fast Description      # FAST (256x256, ~3s)
/image-quality Description   # QUALITY (1024x1024, ~45s)
/image-ultra Description     # ULTRA (1024x1024, ~120s)
```

## 🐛 Troubleshooting

### "All providers exhausted"
Check one env var is set:
```bash
echo $GROQ_API_KEY $HUGGINGFACE_API_KEY $OPENAI_API_KEY
docker ps | grep ollama
```

### Ollama connection error
```bash
docker start ollama
curl http://localhost:11434/api/tags
```

### Timeout
Use faster quality:
```
/image-fast description
```

### Memory error
- Use FAST quality
- Use cloud providers instead of local
- Close other apps

## 📖 Documentation

- Full docs: [demo-ui/docs/IMAGE-GENERATION.md](../docs/IMAGE-GENERATION.md)
- Architecture: [IMAGE-GENERATION-IMPLEMENTATION.md](../IMAGE-GENERATION-IMPLEMENTATION.md)
- Code: [demo-ui/services/image_processor.py](../services/image_processor.py)
- Tests: [tests/unit/test_image_processor.py](../../tests/unit/test_image_processor.py)

## 🔧 Advanced Usage

### Python API

```python
from services.image_processor import get_image_processor, ImageProvider, ImageQuality

processor = get_image_processor()

# Generate image
image_data = await processor.generate_image(
    "farm landscape",
    provider=ImageProvider.GROQ,
    quality=ImageQuality.QUALITY
)

# Save to file
if image_data:
    with open("farm.png", "wb") as f:
        f.write(image_data)
```

### Chainlit Integration

```python
# In @cl.on_message handler
from services.image_processor import get_image_processor

processor = get_image_processor()
image_data = await processor.generate_image(prompt)

if image_data:
    elements = [cl.Image(content=image_data)]
    await cl.Message(
        content=f"Generated: {prompt}",
        elements=elements
    ).send()
```

---

**Quick Links**:
- 📝 Full Docs: [IMAGE-GENERATION.md](../docs/IMAGE-GENERATION.md)
- 🏗️ Architecture: [IMAGE-GENERATION-IMPLEMENTATION.md](../IMAGE-GENERATION-IMPLEMENTATION.md)
- 📦 Code: [image_processor.py](../services/image_processor.py)
- 🧪 Tests: [test_image_processor.py](../../tests/unit/test_image_processor.py)
- 🎮 Commands: [commands.py](../services/commands.py)
