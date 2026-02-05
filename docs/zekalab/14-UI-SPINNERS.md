# 🎨 ALEM Spinner & Loading States Guide

> **Purpose**: Reusable, ALEM-branded loading indicators
> **Location**: `demo-ui/components/spinners.py`
> **CSS**: `demo-ui/public/custom.css` (animations)
> **Status**: Active

---

## 🚀 Quick Start

### Import

```python
from components.spinners import LoadingStates, get_inline_spinner, show_spinner
```

### Basic Usage (Most Common)

```python
# Option 1: Inline text spinner (fastest, simplest)
await response_msg.stream_token(LoadingStates.thinking())

# Option 2: Update existing message
msg = cl.Message(content="")
await msg.send()
await show_spinner(msg, "loading")
```

---

## 📋 Available Spinners

| Type | Azerbaijani Text | Use Case |
|:-----|:-----------------|:---------|
| **thinking** | 🌿 Düşünürəm... | Agent reasoning, LLM processing |
| **loading** | 🌿 Yüklənir... | Loading farm data, fetching info |
| **searching** | 🌿 Axtarıram... | Knowledge base search, document lookup |
| **transcribing** | 🌿 Səsinizi eşidirəm... | Audio-to-text conversion |
| **analyzing** | 🌿 Təhlil edirəm... | Analyzing farm conditions, soil data |
| **generating** | 🌿 Tövsiyələr hazırlayıram... | Generating recommendations |

---

## 🎯 Usage Patterns

### Pattern 1: Simple Text Spinner (Recommended)

**Best for**: Quick loading states, inline indicators

```python
# Show spinner immediately
response_msg = cl.Message(content="", author="ALEM")
await response_msg.send()
await response_msg.stream_token(LoadingStates.thinking())

# Later: update with actual content
response_msg.content = "Buğda əkini üçün ən yaxşı vaxt..."
await response_msg.update()
```

### Pattern 2: Update Existing Message

**Best for**: Multi-step operations where message already exists

```python
msg = cl.Message(content="Starting analysis...")
await msg.send()

# Show spinner
await show_spinner(msg, "analyzing")

# Do work
analysis_result = await analyze_farm_data()

# Clear spinner and show result
await clear_spinner(msg, analysis_result)
```

### Pattern 3: HTML Spinner (Advanced)

**Best for**: Rich visual feedback, longer operations

```python
from components.spinners import get_spinner_html

spinner_html = get_spinner_html("loading", "Torpaq məlumatları yüklənir...")
msg = cl.Message(content=spinner_html)
await msg.send()

# Later: replace with actual content
msg.content = "✅ Məlumatlar yükləndi!"
await msg.update()
```

### Pattern 4: Progress Bar

**Best for**: Long-running tasks with known progress

```python
from components.spinners import get_progress_bar

for i in range(0, 101, 10):
    progress_html = get_progress_bar(i, "Model yüklənir")
    msg.content = progress_html
    await msg.update()
    await asyncio.sleep(0.5)

msg.content = "✅ Model yükləndi!"
await msg.update()
```

### Pattern 5: Multi-Step Indicator

**Best for**: Sequential operations (analysis pipeline)

```python
from components.spinners import get_step_indicator

steps = [
    "Torpaq təhlili",
    "Hava məlumatları",
    "Bitki vəziyyəti",
    "Tövsiyələr",
]

for idx, step_name in enumerate(steps, 1):
    step_html = get_step_indicator(idx, len(steps), step_name)
    msg.content = step_html
    await msg.update()

    # Perform step
    await process_step(step_name)

msg.content = "✅ Təhlil tamamlandı!"
await msg.update()
```

---

## 🎨 Visual Examples

### Text Spinner Output

```
🌿 Düşünürəm...
```

### HTML Spinner Output

```
┌────────────────────────────────────────┐
│ 🌿  Səsinizi eşidirəm...               │
└────────────────────────────────────────┘
```
(Animated with pulsing clover)

### Progress Bar Output

```
┌────────────────────────────────────────┐
│ Model yüklənir                         │
│ ████████████░░░░░░░░░░░░░░ 45%        │
└────────────────────────────────────────┘
```

### Step Indicator Output

```
┌────────────────────────────────────────┐
│ Addım 2/4                          50% │
│ 🌿 Hava məlumatları                   │
│ ██████████████████░░░░░░░░░░░░░░      │
└────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### CSS Animations

All spinners use CSS animations defined in `custom.css`:

- **alem-pulse**: Pulsing opacity/scale (1.5s cycle)
- **alem-spin**: Full rotation (for circular spinners)
- **alem-bounce**: Vertical bounce effect

### Color Scheme

Spinners use ALEM brand colors:
- Primary: `var(--ALİM-green-primary)` (#2D5A27)
- Accent: `var(--ALİM-clover)` (#A8E6CF)
- Background: Semi-transparent green gradients

### Dark Mode

All spinners automatically adapt to dark mode via CSS:
```css
.dark .alem-spinner {
    background: linear-gradient(135deg, rgba(45, 90, 39, 0.2) 0%, rgba(168, 230, 207, 0.15) 100%);
}
```

---

## 📚 API Reference

### `LoadingStates` (Class)

Pre-configured spinner shortcuts:

```python
LoadingStates.thinking()              # "🌿 Düşünürəm..."
LoadingStates.loading_data()          # "🌿 Yüklənir..."
LoadingStates.searching_knowledge()   # "🌿 Axtarıram..."
LoadingStates.transcribing_audio()    # "🌿 Səsinizi eşidirəm..."
LoadingStates.analyzing_farm()        # "🌿 Təhlil edirəm..."
LoadingStates.generating_advice()     # "🌿 Tövsiyələr hazırlayıram..."
```

### `get_inline_spinner(spinner_type)`

Returns simple emoji + text string.

**Args:**
- `spinner_type`: One of `"thinking"`, `"loading"`, `"searching"`, `"transcribing"`, `"analyzing"`, `"generating"`

**Returns:** `str` (e.g., `"🌿 Düşünürəm..."`)

**Example:**
```python
spinner = get_inline_spinner("thinking")
await msg.stream_token(spinner)
```

### `get_spinner_html(spinner_type, message=None)`

Returns HTML with animated spinner.

**Args:**
- `spinner_type`: Spinner type
- `message`: Custom message (optional)

**Returns:** HTML string with CSS animation

**Example:**
```python
html = get_spinner_html("loading", "Farm data loading...")
msg = cl.Message(content=html)
await msg.send()
```

### `get_progress_bar(percentage, label)`

Returns HTML progress bar.

**Args:**
- `percentage`: 0-100
- `label`: Progress label text

**Returns:** HTML progress bar

**Example:**
```python
html = get_progress_bar(75, "Downloading")
```

### `get_step_indicator(current_step, total_steps, step_name)`

Returns HTML multi-step indicator.

**Args:**
- `current_step`: Current step (1-indexed)
- `total_steps`: Total steps
- `step_name`: Name of current step

**Returns:** HTML step indicator

**Example:**
```python
html = get_step_indicator(3, 5, "Processing data")
```

### `show_spinner(message_obj, spinner_type)` (async)

Update message with spinner.

**Example:**
```python
await show_spinner(msg, "loading")
```

### `clear_spinner(message_obj, final_content)` (async)

Replace spinner with final content.

**Example:**
```python
await clear_spinner(msg, "✅ Complete!")
```

---

## ✅ Best Practices

### DO ✓

- Use `LoadingStates` shortcuts for common operations
- Use inline spinners for quick loading states
- Use HTML spinners for longer operations (>2 seconds)
- Always clear spinners after operation completes
- Match spinner type to operation (thinking vs. loading vs. analyzing)

### DON'T ✗

- Don't use multiple spinners simultaneously
- Don't forget to clear/update spinner after operation
- Don't use progress bars without knowing actual progress
- Don't create custom loading text (use spinners module)
- Don't use generic emojis (🔄, ⏳) — use ALEM brand (🌿)

---

## 🔄 Migration Guide

### Old Pattern (Generic)

```python
# ❌ Old way
await response_msg.stream_token("🔄 ")
thinking_msg = cl.Message(content="🎤 Səsinizi eşidirəm...")
```

### New Pattern (ALEM Branded)

```python
# ✅ New way
await response_msg.stream_token(LoadingStates.thinking())
thinking_msg = cl.Message(content=LoadingStates.transcribing_audio())
```

---

## 📊 Performance Notes

- **Text spinners**: Instant (no rendering overhead)
- **HTML spinners**: ~5ms render time (negligible)
- **Progress bars**: Update every 100-200ms for smooth animation
- **CSS animations**: Hardware-accelerated (smooth even on mobile)

---

## 🎯 Common Use Cases

| Operation | Spinner Type | Example Code |
|:----------|:-------------|:-------------|
| **LLM thinking** | `thinking` | `LoadingStates.thinking()` |
| **Loading farm data** | `loading` | `LoadingStates.loading_data()` |
| **Knowledge base search** | `searching` | `LoadingStates.searching_knowledge()` |
| **Audio transcription** | `transcribing` | `LoadingStates.transcribing_audio()` |
| **Soil analysis** | `analyzing` | `LoadingStates.analyzing_farm()` |
| **Generating advice** | `generating` | `LoadingStates.generating_advice()` |

---

## 📝 Examples in Codebase

### Audio Transcription

**File**: [app.py](../app.py#L1224)

```python
thinking_msg = cl.Message(content=LoadingStates.transcribing_audio())
await thinking_msg.send()

# Transcribe audio
transcription = await transcribe_audio_whisper(audio_data)

# Clear spinner
await thinking_msg.remove()
```

### API Call

**File**: [app.py](../app.py#L1573)

```python
await response_msg.stream_token(LoadingStates.thinking())

result = await api_client.chat(...)

response_msg.content = result.content
await response_msg.update()
```

---

**Document Version**: 1.0
**Last Updated**: January 19, 2026
**Maintainer**: ZekaLab ALEM Team
