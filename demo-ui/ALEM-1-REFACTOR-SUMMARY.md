# 🚀 ALEM 1 — Agent Naming & Chainlit Architecture Refactor

**Date:** January 19, 2026  
**Changes:** Agent renamed to ALEM 1, deprecated stale action callbacks, organized code natively

---

## 📌 What is ALEM?

**ALEM** = **Azərbaycan LLM Ekosistem Matrisi** (Azerbaijani LLM Ecosystem Matrix)

This acronym reflects:
- 🇦🇿 **Azərbaycan** — Azerbaijan-first approach
- 🧠 **LLM** — Large Language Model (AI backbone)
- 🔌 **Ekosistem** — Integrated ecosystem (Chainlit + LangGraph + Langfuse)
- 🏗️ **Matrisi** — Four-tier infrastructure matrix (Groq/Gemini/AzInTelecom/On-Prem)

**ALEM 1** = Production version (like GPT-4, Gemini 2.0, Claude 3.5)  
**Full Name:** "ALEM 1 — Yonca AI Assistant"  
**Tagline:** "Sizin ağıllı kənd təsərrüfatı köməkçiniz" (Your intelligent agricultural assistant)

---

## ✅ Changes Made

### 1. **Agent Identity Renamed to ALEM 1**

| File | Changes |
|------|---------|
| [config.toml](.chainlit/config.toml#L43) | `name = "ALEM 1"` |
| [config.toml](.chainlit/config.toml#L144) | `description = "ALEM 1 — Yonca AI Assistant..."` |
| [app.py](app.py#L576) | `"welcome": "**ALEM 1 — Yonca AI Köməkçisinə xoş gəlmisiniz!**..."` |
| [app.py](app.py#L775) | `author="ALEM 1"` in welcome message |
| [app.py](app.py#L1069) | `author="ALEM 1"` in response loop |
| [custom.css](public/custom.css#L68) | `.cl-message[data-author="ALEM 1"]` |

### 2. **Avatar System**

| Avatar | Location | Purpose |
|--------|----------|---------|
| **ALEM 1** | [alem_1.svg](public/avatars/alem_1.svg) | AI assistant (4-leaf clover + "1" badge) |
| **General** | [general.svg](public/avatars/general.svg) | Chat profile: General farmer |
| **Cotton** | [cotton.svg](public/avatars/cotton.svg) | Chat profile: Cotton specialist |
| **Wheat** | [wheat.svg](public/avatars/wheat.svg) | Chat profile: Wheat specialist |
| **Expert** | [expert.svg](public/avatars/expert.svg) | Chat profile: Agronomist |

**How Chainlit Uses Avatars:**
- Author name → filename conversion: `ALEM 1` → `alem_1.svg`
- Automatically displayed next to all messages
- No custom code needed!

### 3. **Stale Action Callbacks Removed**

**Deprecated Code:**
```python
# ❌ OLD (custom action callbacks)
@cl.action_callback("weather")
async def on_weather_action(action: cl.Action):
    await action.remove()
    await cl.Message(content="...", author="user").send()
    await on_message(...)
```

**Why Deprecated:**
- Not profile-aware (all users see same buttons)
- Redundant with `@cl.set_starters` (Chainlit native)
- Extra code to maintain

**New Approach:**
```python
# ✅ NEW (profile-aware starters via @cl.set_starters)
@cl.set_starters
async def set_starters(current_user, chat_profile):
    if chat_profile == "cotton":
        return [
            cl.Starter("🌤️ Hava", "Bu günkü hava proqnozu necədir?", ...),
            ...
        ]
```

**Benefits:**
- ✅ Profile-specific starters (cotton farmers see different actions)
- ✅ Cleaner UX (users expect Chainlit starters)
- ✅ Less code (no custom action callbacks)
- ✅ Better flow (Click starter → Message auto-sent → `@on_message` handles it)

### 4. **Chainlit Architecture Documentation**

**New File:** [CHAINLIT-NATIVE-ARCHITECTURE.md](CHAINLIT-NATIVE-ARCHITECTURE.md)

Comprehensive guide covering:
- ✅ Why native architecture matters
- ✅ Core Chainlit concepts (Chat Profiles, Starters, Settings, Audio)
- ✅ ALEM 1 integration points
- ✅ Anti-patterns to avoid
- ✅ Message flow diagrams
- ✅ Testing checklist

---

## 🏗️ Chainlit Native Architecture

### The Pattern

```
┌─ Lifecycle Events ──────────────────────────────────────┐
│  @on_chat_start                                         │
│  ├─ Initialize session + user context                   │
│  ├─ Call @set_chat_profiles → Show profile selector    │
│  ├─ Call @setup_chat_settings → Show settings panel    │
│  └─ Send welcome message (author="ALEM 1")             │
│                                                         │
│  @on_message                                            │
│  ├─ Get chat_profile from session                      │
│  ├─ Get currency from settings                         │
│  ├─ Route to LangGraph agent                           │
│  └─ Stream response (author="ALEM 1")                  │
│                                                         │
│  @on_settings_update                                    │
│  └─ Persist to database + acknowledge                  │
│                                                         │
│  @on_audio_start / @on_audio_chunk / @on_audio_end    │
│  └─ Handle voice input → transcribe → @on_message     │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Purpose | Where Used |
|---------|---------|-----------|
| **Chat Profiles** | Specialized farming roles (cotton/wheat/expert) | Header dropdown |
| **Starters** | Profile-specific quick actions | Below profile selector |
| **Settings** | User preferences (language, currency, units) | Sidebar gear icon |
| **Audio** | Voice input for farmers in field | Microphone button |
| **Avatars** | Visual distinction (ALEM 1 vs User vs Profiles) | Auto-loaded from `author` name |
| **Messages** | All communication (user, ALEM 1, system) | Main chat area |

### File Organization

```
demo-ui/app.py
├── SYSTEM CONSTANTS
│   ├── AZ_STRINGS (localization)
│   ├── PROFILE_STARTERS (per-profile quick actions)
│   ├── PROFILE_PROMPTS (per-profile system prompt)
│   └── CONSTANTS (API keys, model config)
│
├── CHAINLIT LIFECYCLE
│   ├── @on_chat_start (initialize)
│   ├── @set_chat_profiles (profile selector)
│   ├── @set_starters (quick actions)
│   ├── @setup_chat_settings (preferences)
│   └── @on_settings_update (save preferences)
│
├── AUDIO INPUT
│   ├── @on_audio_start (recording started)
│   ├── @on_audio_chunk (data received)
│   ├── @on_audio_end (recording finished)
│   └── transcribe_audio_whisper() (API call)
│
├── MESSAGE ROUTING
│   ├── @on_message (main chat loop)
│   └── agent_chain() (LangGraph integration)
│
└── UTILITIES
    ├── load_user_settings() (fetch persisted)
    └── save_user_settings() (persist to DB)
```

---

## 🧪 Testing the Changes

### 1. **Avatar System**
- [ ] Welcome message shows ALEM 1 avatar (4-leaf clover)
- [ ] User messages show Google profile photo
- [ ] Profile selector shows 4 profile avatars

### 2. **Profile System**
- [ ] Click profile → starters update
- [ ] Each profile has different starters
- [ ] Profile stored in session

### 3. **Starters (No More Action Callbacks!)**
- [ ] Click starter → message auto-sent
- [ ] No separate UI interaction needed
- [ ] Response comes from `@on_message` normally

### 4. **Settings**
- [ ] Currency setting works (₼ AZN / $ USD / € EUR)
- [ ] Changes persist across sessions
- [ ] Settings reflected in recommendations

---

## 🚫 Anti-Patterns Removed

| ❌ Old Pattern | ✅ New Pattern | Why |
|---|---|---|
| `@cl.action_callback("weather")` | `@cl.set_starters` | Chainlit native |
| Multiple `author` names | `"ALEM 1"` + `"user"` only | Clarity |
| Custom action logic | Let Chainlit + LangGraph handle it | Separation of concerns |
| Hardcoded starters | Profile-aware via dict lookup | Maintainability |

---

## 🎯 Branding Guidelines

### User-Facing Names
- ✅ **"ALEM 1"** — Official product name (like GPT-4, Gemini 2.0)
- ✅ **"Yonca AI Assistant"** — Full description
- ✅ **"Sizin ağıllı kənd təsərrüfatı köməkçiniz"** — Azerbaijani tagline

### Internal Names (Development)
- ❌ "Sidecar" (internal ZekaLab term)
- ❌ "DigiRella" (client name)
- ❌ "Digital Umbrella" (business unit)
- ✅ "ALEM" (product ecosysystem)
- ✅ "Yonca AI" (Yonca implementation)

### In Code
```python
# Correct
author = "ALEM 1"  # For Chainlit messages
product_name = "ALEM 1"  # In UI
system_prompt = "Sen ALEM 1-sin..."  # In prompts

# Incorrect
author = "Yonca AI"  # ❌ Old name
product_name = "Sidecar"  # ❌ Internal term
system_prompt = "Sen Yonca AI-sin..."  # ❌ Use ALEM 1
```

---

## 📊 Summary of Files Changed

| File | Changes |
|------|---------|
| [app.py](app.py) | Renamed agent to ALEM 1, removed stale action callbacks, added architecture notes |
| [config.toml](.chainlit/config.toml) | Updated product name and description |
| [custom.css](public/custom.css) | Updated message styling selectors |
| [alem_1.svg](public/avatars/alem_1.svg) | **NEW** — ALEM 1 avatar with clover + "1" badge |
| [CHAINLIT-NATIVE-ARCHITECTURE.md](CHAINLIT-NATIVE-ARCHITECTURE.md) | **NEW** — Comprehensive architecture guide |

---

## 🔄 Next Steps

1. **Test in UI:**
   - [ ] Refresh browser cache (Ctrl+Shift+R)
   - [ ] Verify ALEM 1 avatar shows
   - [ ] Verify profile selector works
   - [ ] Verify starters update per profile

2. **Update Documentation:**
   - [ ] Update README.md to mention ALEM 1
   - [ ] Update user-facing docs
   - [ ] Update API documentation

3. **Update Prompts:**
   - [ ] Update system prompts to reference "ALEM 1" instead of "Yonca AI"
   - [ ] Verify Azerbaijani naturalness

4. **Update Tests:**
   - [ ] Check any tests referencing old names
   - [ ] Update test assertions for author names

---

## 📚 Related Documentation

- [Chainlit Native Architecture](CHAINLIT-NATIVE-ARCHITECTURE.md)
- [Chainlit Docs — Chat Profiles](https://docs.chainlit.io/concepts/chat-profiles)
- [Chainlit Docs — Starters](https://docs.chainlit.io/concepts/starters)
- [Chainlit Docs — Avatars](https://docs.chainlit.io/customisation/avatars)
- [ALEM Infrastructure Tiers](../docs/zekalab/16-ALEM-INFRASTRUCTURE-TIERS.md)

---

**Questions?** Review [CHAINLIT-NATIVE-ARCHITECTURE.md](CHAINLIT-NATIVE-ARCHITECTURE.md) for complete architecture walkthrough.
