# 🏗️ Chainlit Native Architecture Guide

> **Purpose:** Document how our Chainlit app is organized around native Chainlit concepts, not custom implementations.

## Why Native Architecture?

✅ **Reduces complexity** — Use Chainlit's built-in features instead of custom UI code
✅ **Better UX** — Users get expected Chainlit behaviors automatically
✅ **Maintainability** — Less custom code to maintain
✅ **Performance** — Chainlit's features are optimized

---

## 📊 Chainlit Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CHAINLIT APPLICATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  🎯 MESSAGE FLOW                                      │  │
│  │  ┌─────────────┐    ┌──────────────┐   ┌──────────┐ │  │
│  │  │   on_chat   │───▶│ set_starters │──▶│Greeting  │ │  │
│  │  │   _start    │    └──────────────┘   │ Message  │ │  │
│  │  └─────────────┘                       │ + Avatar │ │  │
│  │         │                              └──────────┘ │  │
│  │         │                                   │        │  │
│  │         ├─── set_chat_profiles ────────┐   │        │  │
│  │         │    (profile selector)        │   │        │  │
│  │         │    - General                 │   │        │  │
│  │         │    - Cotton Specialist       │   │        │  │
│  │         │    - Wheat Specialist        │   │        │  │
│  │         │    - Expert                  │   │        │  │
│  │         │                              │   │        │  │
│  │         └──────────────────────────────┘   │        │  │
│  │                                            ▼        │  │
│  │                                      🌾 ALEM 1      │  │
│  │                                    Welcome Shown     │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  💬 USER INTERACTION                                  │  │
│  │                                                      │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │  Chat Profile Selector                      │   │  │
│  │  │  [🌿 General] [🏵️ Cotton] [🌾 Wheat] [🔬 Expert]  │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │         │         │          │         │           │  │
│  │         └────┬────┴──────────┴────┬────┘           │  │
│  │              ▼                    ▼                │  │
│  │         @set_starters       @on_chat_start        │  │
│  │         (profile-aware)     (initialize)          │  │
│  │                                                   │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │  Quick Action Starters                   │   │  │
│  │  │  ┌─────────────────────────────────────┐ │   │  │
│  │  │  │ 🌤️ Hava    (Weather)                 │ │   │  │
│  │  │  │ 📋 Subsidiya (Subsidy Check)         │ │   │  │
│  │  │  │ 💧 Suvarma   (Irrigation Schedule)   │ │   │  │
│  │  │  └─────────────────────────────────────┘ │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │              │                                    │  │
│  │              └─── User Clicks ─────────────┐    │  │
│  │                                            ▼    │  │
│  │  ┌──────────────────────────────────────────┐   │  │
│  │  │  @on_message (Main Chat Loop)            │   │  │
│  │  │  - Get chat_profile from session         │   │  │
│  │  │  - Get currency from settings            │   │  │
│  │  │  - Route to LangGraph agent              │   │  │
│  │  │  - Stream response with avatar           │   │  │
│  │  └──────────────────────────────────────────┘   │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ⚙️ SETTINGS (Sidebar)                            │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │ 🌐 Language (Azərbaycanca / English / Русский) │ │  │
│  │  │ 💰 Currency (₼ AZN / $ USD / € EUR)         │ │  │
│  │  │ 📊 Detail Level (Qısa / Orta / Ətraflı)    │ │  │
│  │  │ 📏 Units (Metrik / Yerli)                  │ │  │
│  │  │ 🔔 Notifications (Toggle)                  │ │  │
│  │  │ 📖 Show Sources (Toggle)                   │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  Persisted via @on_settings_update + data_layer  │  │
│  │                                                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 ALEM 1 Integration Points

### 1. **Agent Identity** (`author="ALEM 1"`)
- All AI responses use `author="ALEM 1"`
- Avatar automatically loaded from `/public/avatars/alem_1.svg`
- Chainlit distinguishes participants by avatar + name

### 2. **Chat Profiles** (`@cl.set_chat_profiles`)
- Each profile has its own avatar, system prompt, and starters
- Profile selection triggers `set_starters` to update quick actions
- Profile stored in `cl.user_session["chat_profile"]`
- Included in Langfuse tags: `profile:cotton`, `profile:wheat`, etc.

### 3. **Starters** (`@cl.set_starters`)
- Profile-specific quick actions (weather, subsidy, irrigation)
- **NOT** custom action callbacks — use native `@cl.set_starters`
- Each starter is a profile-relevant suggestion
- User clicks → message sent → `@on_message` triggered normally

### 4. **Settings** (`@cl.on_settings_update`)
- Language, Currency, Detail Level, Units, Notifications, Show Sources
- Automatically persisted to database via data_layer
- Retrieved on `@on_chat_start`

### 5. **Audio Input** (`@cl.on_audio_start`, `@cl.on_audio_chunk`, `@cl.on_audio_end`)
- Native Chainlit audio recording
- Transcribed via Whisper
- Converted to text message → `@on_message` flow

### 6. **Message Flow** (`@on_chat_start`, `@on_message`)
- `@on_chat_start`: Initialize session, send welcome, set profiles/starters/settings
- `@on_message`: Get profile + settings from session, route to LangGraph, stream response
- Response has `author="ALEM 1"` + proper avatar

---

## 🚫 Anti-Patterns (What NOT to Do)

| ❌ Don't | ✅ Do Instead | Why |
|---------|--------------|-----|
| Custom action callbacks | Use `@cl.set_starters` | Starters are profile-aware, cleaner UX |
| Multiple `author` names | Use only `ALEM 1` and `user` | Confusion about who's speaking |
| Store profile in message metadata | Use `cl.user_session["chat_profile"]` | Session is designed for this |
| Hardcode starters in `on_chat_start` | Return from `@cl.set_starters` | Chainlit handles the UI binding |
| Custom UI elements | Use Chainlit native (Audio, Starters, Settings, Elements) | Chainlit provides these out-of-box |

---

## 📋 File Organization

```
demo-ui/
├── app.py                          # Main Chainlit application (THIS FILE)
│   ├── SYSTEM CONSTANTS
│   ├── CHAINLIT LIFECYCLE
│   │   ├── @on_chat_start          # Initialize session
│   │   ├── @set_chat_profiles      # Return profile list
│   │   ├── @set_starters           # Return profile-specific starters
│   │   ├── @on_chat_start (setup_chat_settings)  # Initialize settings
│   │   └── @on_settings_update     # Handle setting changes
│   │
│   ├── AUDIO INPUT
│   │   ├── @on_audio_start         # Recording started
│   │   ├── @on_audio_chunk         # Audio data received
│   │   ├── @on_audio_end           # Recording finished
│   │   └── transcribe_audio_whisper()  # Whisper API call
│   │
│   ├── MESSAGE ROUTING
│   │   ├── @on_message             # Main chat loop
│   │   └── agent_chain()           # LangGraph integration
│   │
│   └── UTILITIES
│       ├── load_user_settings()    # Fetch from data_layer
│       └── save_user_settings()    # Persist to data_layer
│
├── data_layer.py                   # SQLAlchemy data persistence
├── config.py                       # Yonca backend API client
│
├── .chainlit/
│   ├── config.toml                 # Audio enabled, HTML unsafe, etc.
│   └── oauth.json                  # Google OAuth (FREE scopes)
│
├── public/
│   ├── avatars/
│   │   ├── alem_1.svg              # AI assistant avatar (4-leaf clover)
│   │   ├── general.svg             # Chat profile: General farmer
│   │   ├── cotton.svg              # Chat profile: Cotton specialist
│   │   ├── wheat.svg               # Chat profile: Wheat specialist
│   │   └── expert.svg              # Chat profile: Agronomist expert
│   │
│   ├── elements/                   # Starter icons
│   │   ├── weather.svg             # 🌤️ Weather icon
│   │   ├── water.svg               # 💧 Irrigation icon
│   │   └── ... (11 more)
│   │
│   ├── custom.css                  # Styling for ALEM 1 messages
│   └── profile-enhancer.js         # Google profile photo enhancement
│
└── Dockerfile                      # Container build
```

---

## 🔄 Message Flow (Sequence Diagram)

```
User                    Chainlit UI              app.py                LangGraph Agent
  │                        │                       │                         │
  │   1. First Load         │                       │                         │
  │   (no messages)         │                       │                         │
  ├──────────────────────▶  │                       │                         │
  │                        │   2. @on_chat_start   │                         │
  │                        ├──────────────────────▶│                         │
  │                        │                       │  3. Initialize session, │
  │                        │                       │     profile, starters   │
  │                        │                       │     settings            │
  │                        │   4. Send welcome msg │                         │
  │   5. See welcome       │◀──────────────────────┤                         │
  │      + profile picker  │   (author="ALEM 1")   │                         │
  │      + starters        │   + avatar            │                         │
  │                        │                       │                         │
  │  6. Selects profile    │                       │                         │
  │  OR clicks starter     │                       │                         │
  ├──────────────────────▶ │                       │                         │
  │                        │   7. Message event    │                         │
  │                        ├──────────────────────▶│                         │
  │                        │                       │  8. Get chat_profile,   │
  │                        │                       │     settings from       │
  │                        │                       │     session             │
  │                        │                       │  9. Call LangGraph      │
  │                        │                       ├────────────────────────▶│
  │                        │                       │                         │
  │                        │                       │                         │
  │                        │                       │                    10. Generate
  │                        │                       │                        response
  │  11. Stream response   │     12. Stream        │◀────────────────────────┤
  │  with ALEM 1 avatar    │◀────────────────────────────────────────────────┤
  │                        │    (author="ALEM 1")  │                         │
  │                        │    (avatar shows)     │                         │
  │                        │                       │                         │
  │  13. See Langfuse      │                       │  14. Send Langfuse tags │
  │      trace            │                       │     + profile metadata  │
  │                        │                       │     + currency setting  │
```

---

## 🧪 Testing Checklist

- [ ] Profile selector shows 4 profiles with correct avatars
- [ ] Each profile has different starters (weather/subsidy/irrigation)
- [ ] Each profile has different system prompt (visible in responses)
- [ ] Settings persist across sessions
- [ ] Audio input works (browser permission required)
- [ ] Langfuse shows correct profile + currency tags
- [ ] ALEM 1 avatar shows next to all assistant messages
- [ ] User avatar (from Google OAuth) shows next to user messages
- [ ] Currency setting affects recommendation prices

---

## 📚 Related Documentation

- [Chainlit Concepts](https://docs.chainlit.io/concepts)
- [Chat Profiles](https://docs.chainlit.io/concepts/chat-profiles)
- [Starters](https://docs.chainlit.io/concepts/starters)
- [Settings](https://docs.chainlit.io/concepts/chat-settings)
- [Audio](https://docs.chainlit.io/concepts/audio)
- [Avatars](https://docs.chainlit.io/customisation/avatars)
- [Data Layer](https://docs.chainlit.io/data-persistence/overview)
