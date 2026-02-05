# 🏗️ Chainlit Native Architecture (Post-Refactoring)

**Pure Chainlit Native - No Custom JS Overlays**

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   USER AUTHENTICATION                       │
│  Google OAuth → Email, Name, Picture (CHAINLIT NATIVE)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              JIT PERSONA PROVISIONING                       │
│  (on_chat_start → Generate synthetic farm identity)         │
│                                                             │
│  📋 ALEM Persona:                                          │
│  ├─ full_name: PX8 Studio                                 │
│  ├─ fin_code: 10AYNG3                                     │
│  ├─ region: Lənkəran                                      │
│  ├─ crop_type: Alma                                       │
│  ├─ total_area_ha: 10.8                                   │
│  └─ ektis_verified: true                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼ (Store in session)
         ┌───────────────────────────────────┐
         │ cl.user_session["alim_persona"]   │ ← NOT DISPLAYED
         └───────────────────┬───────────────┘
                             │
         ┌───────────────────┴─────────────────┐
         │                                     │
         ▼                                     ▼
    ┌─────────────────────┐         ┌──────────────────────┐
    │ Expertise Detection │         │ System Prompt Build  │
    │ (services/expertise)│         │ (services/expertise) │
    │ detect_expertise()  │         │ build_combined_      │
    │ From: crop_type     │         │ system_prompt()      │
    │ Returns: ["general",│         │                      │
    │   "orchard"]        │         │ Uses: expertise      │
    │                     │         │ Results: customized  │
    └──────────┬──────────┘         │ ALEM behavior        │
               │                    └──────────┬───────────┘
               │                              │
               ▼                              ▼
         ┌──────────────────┐         ┌─────────────────┐
         │  Settings Panel  │         │  Chat Response  │
         │  (Multi-select)  │         │  Customization  │
         │                  │         │                 │
         │ 🧠 Expertise     │         │ Context-aware   │
         │ Areas pre-set    │         │ advice generation
         │ per persona      │         └─────────────────┘
         └──────────────────┘
```

---

## 💾 Data Persistence Layer

ALİM uses **PostgreSQL** for all data storage, including user-uploaded files.

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Users & Sessions | PostgreSQL | Chainlit native |
| Conversations | PostgreSQL | Thread history |
| **File Uploads** | PostgreSQL (BYTEA) | Twelve-Factor App compliance |

> [!NOTE]
> We **do not** use Chainlit's default `.files/` local storage.
> This is disabled via `.chainlitignore` for production cloud deployments.
> See: [Production Storage Architecture](11-CHAINLIT-STRUCTURE.md#-production-storage-architecture)

## 🖥️ UI Layer (Pure Chainlit Native)

### What User Sees (No Custom Overlays)

```
┌─────────────────────────────────────────────────────────────┐
│ [🌿 ALEM 1]  [Menu]                     [👤] [⚙️] [Theme] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Chat Area (Focus: Clean Conversation)                     │
│  ─────────────────────────────────────────────────────     │
│                                                             │
│  🌾 Profile Selector                                       │
│  ┌──────────┬──────────┬──────────┬──────────┐            │
│  │ General  │  Cotton  │  Wheat   │ Expert   │ ← Farm     │
│  └──────────┴──────────┴──────────┴──────────┘   Context  │
│                                                             │
│  💬 Message Thread                                         │
│  ┌──────────────────────────────────────────────┐         │
│  │ ALEM 1: Salam! Sizin aqronomam...            │         │
│  │ (Response tailored to crop + expertise)       │         │
│  └──────────────────────────────────────────────┘         │
│                                                             │
│  ⚡ Starters (Profile-Aware)                              │
│  ┌─────────────────┬──────────────┬──────────────┐        │
│  │ 🌤️ Hava         │ 💧 Suvarma   │ 💰 Subsidiya│        │
│  └─────────────────┴──────────────┴──────────────┘        │
│                                                             │
│  📝 Message input...                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [💬 Threads]  [🔍 Search]  [📁 Files]  [📊 Analytics]      │
└─────────────────────────────────────────────────────────────┘

⚙️  Settings (Right Panel - Slide Out)
┌──────────────────────────────┐
│ Chat Settings                │
│                              │
│ 🧠 Expertise Areas [▼]       │
│    ☑ General                 │ ← Smart default
│    ☑ Orchard (Alma)          │   from persona
│    ☐ Wheat                   │
│                              │
│ 🌍 Language: Azərbaycanca    │
│ 💰 Currency: ₼ AZN          │
│ 📊 Detail: Orta              │
│ 📏 Units: Metrik             │
│ 🔔 Notifications: ON         │
└──────────────────────────────┘

👤 User Profile (Dropdown - Pure Native)
┌──────────────────────────────┐
│ 🖼️  [Google Photo]            │
│ Name: Developer User         │
│ Email: user@domain.com       │
│ 🔐 Verified                  │
│ 🌍 Locale: az                │
│ ────────────────────────     │
│ [🔓 Logout]                  │
└──────────────────────────────┘
```

---

## 🔄 Where Farm Context Influences Responses

### 1️⃣ **Settings Panel**
```python
# default_expertise from persona's crop_type
MultiSelect(
    id="expertise_areas",
    initial_value=["General", "Orchard (Alma)"],  # ← Auto-set!
    description="Hansı sahələrdə məsləhət almaq istəyirsiniz?",
)
```

### 2️⃣ **Profile Selector**
```python
@cl.set_chat_profiles
async def chat_profiles():
    # Still creates all 4 profiles, but expertise area
    # multi-select pre-configures based on persona
    return [
        cl.ChatProfile(name="general", ...),
        cl.ChatProfile(name="cotton", ...),
        # User's persona influences which are "natural" choices
    ]
```

### 3️⃣ **System Prompt**
```python
# In on_chat_start():
default_expertise = detect_expertise_from_persona(alim_persona_dict)
# Returns: ["general", "orchard"] if crop_type="Alma"

profile_prompt = build_combined_system_prompt(default_expertise)
# Customizes ALEM's system instructions for this expertise

cl.user_session.set("profile_prompt", profile_prompt)
```

### 4️⃣ **Message Responses**
```python
@cl.on_message
async def on_message(message: cl.Message):
    expertise_areas = cl.user_session.get("expertise_areas")
    # Uses expertise to customize response generation
    # Example: If "orchard" → include apple-specific advice
```

---

## ✅ Verification Checklist

- [x] Persona still created ✓
- [x] Persona still stored in session ✓
- [x] Expertise detection still works ✓
- [x] System prompt still customized ✓
- [x] Settings still smart-configured ✓
- [x] No custom JS ✓
- [x] No custom profile dropdown overlay ✓
- [x] No vertical persona card display ✓
- [x] Chat UI clean and focused ✓
- [x] Code is maintainable ✓

---

## 🎯 Key Principle

**Farm context is invisible but active.**

The ALEM persona doesn't need to be displayed to be influential. It works behind the scenes to:
- Configure smart defaults
- Customize system prompts
- Tailor responses
- Enhance user experience

This is **better UI design** because:
1. ✅ Information is shown when relevant (in responses/settings)
2. ✅ UI stays clean and focused
3. ✅ Context is implicit (simpler for users)
4. ✅ Code is maintainable (no DOM hacks)
5. ✅ Chainlit native = future-proof

---

## 🚀 This Is The Chainlit Way

You've now embraced the **native Chainlit philosophy**:

```
❌ Custom JS patches
❌ DOM manipulation
❌ Overlay curtains

✅ Session storage
✅ Native UI components
✅ Implicit context application
✅ Out-of-the-box quality
```

Your app is now **production-ready** and **framework-aligned**.
