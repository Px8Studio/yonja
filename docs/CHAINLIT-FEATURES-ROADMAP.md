# Yonca AI — Chainlit Native Features Roadmap

> **Status**: Implementation Plan  
> **Priority**: P1 (High Value, Native Features)  
> **Effort**: ~2-3 sprints

## 📋 Overview

This document outlines the native Chainlit features we should enable in Yonca AI. These are **built-in capabilities** that require minimal custom code — just configuration and callbacks.

---

## ✅ Currently Implemented

| Feature | Status | Location |
|---------|--------|----------|
| OAuth (Google) | ✅ Active | `app.py` + `.env` |
| Data Persistence | ✅ Active | `data_layer.py` (SQLAlchemy) |
| Messages | ✅ Active | Throughout app |
| Actions (Buttons) | ✅ Active | Weather, Subsidy, Irrigation |
| Chat Settings | ✅ Active | Language selector |
| Element Sidebar | ✅ Active | Dashboard panel |
| Custom CSS | ✅ Active | `custom.css` |
| Custom JS | ✅ Active | `profile-enhancer.js` |
| Theme | ✅ Active | `theme.json` |
| File Upload | ✅ Enabled | Config only |
| HTML in Messages | ✅ Enabled | Dashboard cards |
| Chain of Thought | ✅ Enabled | `cot = "full"` |

---

## 🎯 Phase 1: Audio Input (Voice for Farmers)

### Why This Matters
Farmers in the field often have dirty hands or are busy with equipment. Voice input lets them ask questions hands-free in Azerbaijani.

### Implementation

**1. Enable in config.toml:**
```toml
[features.audio]
    enabled = true
    sample_rate = 24000
```

**2. Add audio handler in app.py:**
```python
@cl.on_audio_start
async def on_audio_start():
    """Called when user starts recording audio."""
    return True  # Allow recording

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    """Process audio chunks for speech-to-text."""
    # Option A: Use Whisper locally via Ollama
    # Option B: Use Azure Speech Services
    # Option C: Use Google Cloud Speech-to-Text
    pass

@cl.on_audio_end
async def on_audio_end(elements: list[cl.Audio]):
    """Called when audio recording ends."""
    # Transcribe and send as message
    transcription = await transcribe_audio(elements)
    if transcription:
        msg = cl.Message(content=transcription)
        await msg.send()
        await on_message(msg)  # Process as regular message
```

**3. Speech-to-Text Options:**
- **Whisper (Local)**: Free, private, supports Azerbaijani
- **Azure Speech**: Pay-per-use, excellent Azerbaijani support
- **Google STT**: Pay-per-use, good quality

### Estimated Effort: 1 day

---

## 🎯 Phase 2: Chat Profiles (Farmer Personas)

### Why This Matters
Different users have different needs. A cotton farmer needs different advice than a wheat farmer.

### Implementation

**1. Define profiles in app.py:**
```python
@cl.set_chat_profiles
async def chat_profiles(current_user: cl.User):
    return [
        cl.ChatProfile(
            name="general",
            display_name="🌾 Ümumi Kömək",
            markdown_description="Ümumi kənd təsərrüfatı məsələləri üçün",
            icon="/public/avatars/general.png",
            default=True,
            starters=[
                cl.Starter(
                    label="Hava proqnozu",
                    message="Bu həftə üçün hava proqnozu necədir?",
                    icon="☀️"
                ),
                cl.Starter(
                    label="Suvarma",
                    message="Sahəmi nə vaxt suvarmalıyam?",
                    icon="💧"
                ),
            ]
        ),
        cl.ChatProfile(
            name="cotton",
            display_name="🥬 Pambıqçılıq",
            markdown_description="Pambıq becərmə üzrə ixtisaslaşmış köməkçi",
            icon="/public/avatars/cotton.png",
            starters=[
                cl.Starter(
                    label="Pambıq əkini",
                    message="Pambıq əkini üçün ən yaxşı vaxt nədir?",
                    icon="🌱"
                ),
            ]
        ),
        cl.ChatProfile(
            name="wheat",
            display_name="🌾 Taxılçılıq",
            markdown_description="Buğda və arpa becərmə üzrə köməkçi",
            icon="/public/avatars/wheat.png",
        ),
        cl.ChatProfile(
            name="expert",
            display_name="🔬 Ekspert Rejimi",
            markdown_description="Ətraflı texniki məlumat və analiz",
            icon="/public/avatars/expert.png",
        ),
    ]
```

**2. Adjust system prompt based on profile:**
```python
@cl.on_chat_start
async def on_chat_start():
    profile = cl.user_session.get("chat_profile")
    
    if profile == "cotton":
        system_prompt = COTTON_EXPERT_PROMPT
    elif profile == "wheat":
        system_prompt = WHEAT_EXPERT_PROMPT
    elif profile == "expert":
        system_prompt = EXPERT_DETAILED_PROMPT
    else:
        system_prompt = GENERAL_PROMPT
    
    cl.user_session.set("system_prompt", system_prompt)
```

### Estimated Effort: 0.5 day

---

## 🎯 Phase 3: Starters (Quick Actions)

### Why This Matters
Reduce friction for common questions. New users see helpful suggestions immediately.

### Implementation

Already included in Chat Profiles above! Starters appear on the welcome screen.

**Standalone starters (without profiles):**
```python
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Plan my week",
            message="Bu həftə üçün iş planı hazırla",
            icon="📅"
        ),
        cl.Starter(
            label="Weather check",
            message="Hava proqnozu necədir?",
            icon="🌤️"
        ),
        cl.Starter(
            label="Crop advice",
            message="Məhsulum üçün tövsiyələr ver",
            icon="🌱"
        ),
        cl.Starter(
            label="Subsidies",
            message="Hansı subsidiyalardan yararlana bilərəm?",
            icon="💰"
        ),
    ]
```

### Estimated Effort: 0.5 day

---

## 🎯 Phase 4: Image Elements (Farm Visualization)

### Why This Matters
Show satellite imagery, crop disease photos, weather maps.

### Implementation

```python
@cl.on_message
async def on_message(message: cl.Message):
    # ... process message ...
    
    # If response includes map data
    if "weather_map" in response_data:
        weather_image = cl.Image(
            name="weather_map",
            display="inline",
            path=response_data["weather_map_path"],
            # or url=response_data["weather_map_url"]
        )
        await cl.Message(
            content="Bu günkü hava xəritəsi:",
            elements=[weather_image]
        ).send()
```

### Estimated Effort: 0.5 day

---

## 🎯 Phase 5: PDF Reports

### Why This Matters
Generate downloadable farm reports, subsidy applications.

### Implementation

```python
async def generate_farm_report(farm_id: str) -> str:
    """Generate PDF report for farm."""
    # Use ReportLab or WeasyPrint
    pdf_path = f"/tmp/farm_report_{farm_id}.pdf"
    # ... generate PDF ...
    return pdf_path

@cl.action_callback("download_report")
async def on_download_report(action: cl.Action):
    farm_id = cl.user_session.get("farm_id")
    pdf_path = await generate_farm_report(farm_id)
    
    pdf_element = cl.Pdf(
        name="Farm Report",
        display="inline",
        path=pdf_path
    )
    
    await cl.Message(
        content="Sizin təsərrüfat hesabatınız hazırdır:",
        elements=[pdf_element]
    ).send()
```

### Estimated Effort: 1 day

---

## 🎯 Phase 6: Favorites

### Why This Matters
Users can save useful AI responses to reference later.

### Implementation

**1. Enable in config.toml:**
```toml
[features]
favorites = true
```

That's it! Chainlit handles the rest.

### Estimated Effort: 5 minutes

---

## 📊 Implementation Priority

| Phase | Feature | Effort | Value | Priority |
|-------|---------|--------|-------|----------|
| 1 | Audio Input | 1 day | ⭐⭐⭐⭐⭐ | **P0** |
| 2 | Chat Profiles | 0.5 day | ⭐⭐⭐⭐ | **P1** |
| 3 | Starters | 0.5 day | ⭐⭐⭐⭐ | **P1** |
| 4 | Image Elements | 0.5 day | ⭐⭐⭐ | P2 |
| 5 | PDF Reports | 1 day | ⭐⭐⭐ | P2 |
| 6 | Favorites | 5 min | ⭐⭐ | P3 |

---

## 🚀 Let's Start with Audio!

Ready to implement Phase 1 (Audio Input)?

**What we need to decide:**
1. Speech-to-text provider (Whisper local vs cloud)
2. Sample rate (16kHz standard, 24kHz high quality)
3. Language detection (auto-detect or assume Azerbaijani)
