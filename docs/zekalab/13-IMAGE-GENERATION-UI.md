# 🖼️ Image Generation System

Multi-provider image generation for ALEM with local and cloud support.

## 📋 Features

- **Multi-Provider Support**: Automatic fallback through providers
  - 🏠 **Local**: Ollama (on-device, zero cost)
  - ⚡ **Cloud**: Groq (fast, affordable)
  - 🤗 **Cloud**: Hugging Face Inference API
  - 🎨 **Fallback**: OpenAI DALL-E (premium quality)

- **Quality Presets**: Optimized settings for different use cases
  - 🚀 FAST: 256x256, 10 steps (~2-3 seconds)
  - ⚡ STANDARD: 512x512, 20 steps (~10-15 seconds)
  - ✨ QUALITY: 1024x1024, 40 steps (~30-45 seconds)
  - 🌟 ULTRA: 1024x1024, 60 steps (~60-120 seconds)

- **Automatic Prompt Optimization**: Enhances prompts with quality descriptors
- **Graceful Degradation**: Falls back to next provider if primary fails
- **Async/Streaming**: Non-blocking image generation
- **Error Handling**: Comprehensive logging and error recovery

## 🎯 Usage

### Commands

```
/image <description>     Generate image (auto quality)
/img <description>       Generate image (quick alias)
/image                   Show usage and providers
```

### Examples

```
/image A serene farm landscape at sunrise with rolling hills
/img Crops in a field with irrigation system
/image Agricultural equipment in a modern farmhouse
```

## ⚙️ Configuration

### Environment Variables

```bash
# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_IMAGE_MODEL=stable-diffusion-v1-5

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_IMAGE_MODEL=groq-vision-v1

# Hugging Face
HUGGINGFACE_API_KEY=your_hf_api_key
HUGGINGFACE_IMAGE_MODEL=stabilityai/stable-diffusion-2-1

# OpenAI (Fallback)
OPENAI_API_KEY=your_openai_api_key
```

### Provider Priority

Default fallback order:
1. Ollama Local (fastest, free)
2. Groq (fast, cheap)
3. Hugging Face (reliable, free tier)
4. OpenAI (premium, cost)

## 🚀 Getting Started

### 1. Setup Local Provider (Ollama)

```bash
# Pull image model
docker pull ollama/ollama

# Run Ollama with image support
docker run --gpus=all -d -v /path/to/models:/root/.ollama \
  -p 11434:11434 \
  --name ollama ollama/ollama

# Pull a text-to-image model
docker exec ollama ollama pull stable-diffusion-v1-5
```

### 2. Setup Groq Provider (Optional)

Get API key from [console.groq.com](https://console.groq.com)

```bash
export GROQ_API_KEY=your_key
```

### 3. Setup Hugging Face (Optional)

Get token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

```bash
export HUGGINGFACE_API_KEY=your_token
```

### 4. Use in ALEM

```bash
# Start ALEM
chainlit run demo-ui/app.py -w

# In chat, type:
/image A beautiful agricultural landscape
```

## 🏗️ Architecture

### Class Hierarchy

```
ImageProcessor (Main orchestrator)
├── OllamaProvider (Local)
├── GroqProvider (Cloud - Fast)
├── HuggingFaceProvider (Cloud - Free)
└── OpenAIProvider (Cloud - Premium)
```

### Provider Selection Logic

```python
User Request: /image "farm landscape"
         ↓
     Parse Prompt
         ↓
  Optimize Prompt
         ↓
Try Primary Provider (Ollama)
         ↓
   Success? ✅ → Return Image
   Failed? ❌ ↓
         ↓
Try Next Provider (Groq)
         ↓
   Success? ✅ → Return Image
   Failed? ❌ ↓
         ↓
Try Next Provider (HF)
         ↓
   Success? ✅ → Return Image
   Failed? ❌ ↓
         ↓
Try Fallback (OpenAI)
         ↓
   Success? ✅ → Return Image
   All Failed? ❌ → Error Message
```

## 📊 Provider Comparison

| Provider | Speed | Cost | Quality | Setup | Notes |
|----------|-------|------|---------|-------|-------|
| **Ollama** | ⚡⚡⚡ | Free | ⭐⭐⭐ | Docker | Best for privacy, local GPU needed |
| **Groq** | ⚡⚡ | $ | ⭐⭐⭐⭐ | API Key | Good balance of speed/quality |
| **HF** | ⚡ | Free | ⭐⭐⭐⭐ | API Key | Reliable, free tier available |
| **OpenAI** | ⚡⚡ | $$ | ⭐⭐⭐⭐⭐ | API Key | Best quality, premium pricing |

## 🧪 Testing

### Run Tests

```bash
# Run image processor tests
pytest tests/unit/test_image_processor.py -v

# Run with coverage
pytest tests/unit/test_image_processor.py --cov=demo-ui/services/image_processor
```

### Test Coverage

- ImageProcessor: Provider selection, fallback logic
- OllamaProvider: Local generation, error handling
- GroqProvider: Cloud API integration
- HuggingFaceProvider: HF Inference API
- OpenAIProvider: DALL-E integration
- Configuration: Quality presets, prompt optimization
- Singleton: Instance management

## 📖 Code Examples

### Python API

```python
from services.image_processor import (
    get_image_processor,
    ImageProvider,
    ImageQuality,
)

# Get processor (singleton)
processor = get_image_processor()

# Generate image with defaults
image_data = await processor.generate_image(
    "a farm landscape"
)

# Generate with specific provider
image_data = await processor.generate_image(
    "a farm landscape",
    provider=ImageProvider.GROQ,
    quality=ImageQuality.QUALITY,
)

# Save to file
if image_data:
    with open("farm.png", "wb") as f:
        f.write(image_data)
```

### Chainlit Integration

```python
# In app.py @cl.on_message handler
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

## 🔧 Customization

### Add Custom Provider

```python
# Create provider class
class CustomProvider:
    async def generate(
        self,
        prompt: str,
        config: ImageGenerationConfig,
        **kwargs
    ) -> Optional[bytes]:
        """Generate image using custom service."""
        # Implementation
        return image_bytes

# Register provider
from services.image_processor import ImageProcessor
processor = get_image_processor()
processor.providers[ImageProvider.CUSTOM] = CustomProvider()
```

### Modify Quality Presets

```python
processor = get_image_processor()

# Override FAST preset
fast_config = processor._get_quality_config(ImageQuality.FAST)
fast_config.steps = 15  # More steps for better quality
```

## 🐛 Troubleshooting

### "No provider available"

Check environment variables:
```bash
# Test each provider
curl http://localhost:11434/api/tags  # Ollama
echo $GROQ_API_KEY                    # Groq
echo $HUGGINGFACE_API_KEY             # HF
echo $OPENAI_API_KEY                  # OpenAI
```

### Ollama Connection Error

```bash
# Check if Ollama is running
docker ps | grep ollama

# Logs
docker logs ALİM-ollama

# Test API
curl http://localhost:11434/api/tags
```

### Timeout Errors

Increase timeout or use faster quality preset:
```python
# Use FAST instead of QUALITY
await processor.generate_image(
    prompt,
    quality=ImageQuality.FAST
)
```

### Memory Issues

If running out of memory:
- Use FAST quality preset
- Use Groq/HF cloud providers instead of local
- Reduce max_tokens in config

## 📈 Performance Metrics

### Local (Ollama) - GPU
- FAST: ~2-3 seconds (256x256)
- STANDARD: ~10-15 seconds (512x512)
- QUALITY: ~30-45 seconds (1024x1024)

### Groq - Cloud
- FAST: ~5-10 seconds
- STANDARD: ~15-20 seconds
- QUALITY: ~20-30 seconds

### HF - Cloud (Free)
- FAST: ~10-20 seconds
- STANDARD: ~30-60 seconds
- QUALITY: ~60-120 seconds

### OpenAI - Cloud
- All: ~10-60 seconds (depends on queue)

## 🗺️ Roadmap

### Phase 1: Core Implementation ✅
- [x] Multi-provider support
- [x] Quality presets
- [x] Fallback mechanism
- [x] Error handling

### Phase 2: Enhancements 🔄
- [ ] Image caching with Redis
- [ ] Negative prompt customization per command
- [ ] Batch image generation
- [ ] Image variants/styles
- [ ] Image editing (inpainting)
- [ ] NSFW content filtering

### Phase 3: Advanced Features 📋
- [ ] Style presets (watercolor, oil painting, etc.)
- [ ] AR filter generation
- [ ] Prompt history/search
- [ ] Usage analytics
- [ ] Cost tracking
- [ ] Custom model fine-tuning

## 📚 References

- [Ollama Documentation](https://ollama.ai/)
- [Groq Documentation](https://console.groq.com/docs)
- [Hugging Face Inference API](https://huggingface.co/inference-api)
- [OpenAI DALL-E](https://platform.openai.com/docs/guides/images)
- [Stable Diffusion Models](https://huggingface.co/models?other=stable-diffusion)

---

**Last Updated**: 2024-12-20
**Version**: 1.0.0
**Maintainer**: ALEM Development Team
