# 🔧 Alembic Command Fix + Chat Settings UX Enhancement

**Date:** 2026-01-19  
**Issues:**
1. Alembic command not recognized in PowerShell
2. Chat profiles (general/cotton/wheat/expert) should be context-aware based on user persona

---

## Issue 1: Alembic Command Not Recognized

### ❌ Problem:
```powershell
PS C:\Users\rjjaf\_Projects\yonja> alembic upgrade head
alembic: The term 'alembic' is not recognized as a name of a cmdlet, function...
```

### ✅ Solution Options:

#### Option A: Activate Virtual Environment First (RECOMMENDED)
```powershell
# Step 1: Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Step 2: Now alembic command is available
alembic upgrade head
```

#### Option B: Use Full Path (No Activation Needed)
```powershell
# Direct path to alembic in virtual environment
.\.venv\Scripts\alembic.exe upgrade head
```

#### Option C: Use Python Module Syntax
```powershell
# Run alembic as Python module
python -m alembic upgrade head
```

### Why This Happens:
Virtual environments isolate Python packages. When you install `alembic` via `pip install alembic`, it installs the executable in `.venv\Scripts\alembic.exe`. This directory is NOT in your system PATH until you activate the virtual environment.

### Recommended Workflow:
```powershell
# 1. Navigate to project directory
cd C:\Users\rjjaf\_Projects\yonja

# 2. Activate virtual environment (adds .venv\Scripts to PATH)
.\.venv\Scripts\Activate.ps1

# 3. You'll see (.venv) prefix in prompt:
# (.venv) PS C:\Users\rjjaf\_Projects\yonja>

# 4. Now all Python tools are available:
alembic upgrade head
pytest
ruff check src/

# 5. When done, deactivate:
deactivate
```

### One-Liner for Quick Migrations:
```powershell
# Activate + upgrade + deactivate in one command
.\.venv\Scripts\Activate.ps1; alembic upgrade head; deactivate
```

---

## Issue 2: Chat Profiles Should Be Context-Aware

### 🎯 Current Problem:

**Chat Profiles Dropdown (Top of Chat):**
- General
- Cotton Expert
- Wheat Expert
- Advanced Expert

**Issues:**
1. **Static, not persona-aware** — Shown to all users regardless of their farm context
2. **Manual selection** — User must remember to switch profiles
3. **Single-select** — Can't combine expertise (e.g., "I grow cotton AND wheat")
4. **Not in Chat Settings** — Feels disconnected from other preferences

### 💡 Your Insight:
> "We should identify the tags/types that apply to a selected active user and enable them, configure them by default unless changed and overwritten by the user... and wonder whether there would be a better way to incorporate this actually inside the chat settings, so default configured smartly by the app unless changed by the user, **multiple select tho!**"

**This is BRILLIANT.** Here's why:

1. ✅ **ALEM Persona Already Has Crop Context** — We know the user's crop type from their persona
2. ✅ **Chat Settings Already Exist** — Perfect place to consolidate preferences
3. ✅ **Chainlit Supports Multi-Select** — Can use `MultiSelect` widget
4. ✅ **Aligns with EKTİS Multi-Crop Reality** — Real farmers DO grow multiple crops!

---

## 🚀 Proposed Solution: Smart Context-Aware Chat Profiles

### Architecture Changes:

#### 1. Move Profiles to Chat Settings (Multi-Select)
Instead of top-level dropdown, add to chat settings sidebar:

```python
# demo-ui/app.py — Update setup_chat_settings()

@cl.on_chat_start
async def setup_chat_settings(user: cl.User = None):
    """Initialize chat settings with smart defaults from ALEM persona."""
    
    # Load ALEM persona to get user's crop context
    alem_persona = cl.user_session.get("alem_persona")
    
    # Determine smart defaults based on persona
    default_expertise = []
    
    if alem_persona:
        crop_type = alem_persona.crop_type
        experience = alem_persona.experience_level
        
        # Auto-enable relevant expertise areas
        if "Pambıq" in crop_type:  # Cotton
            default_expertise.append("cotton")
        if "Buğda" in crop_type or "Arpa" in crop_type:  # Wheat/Barley
            default_expertise.append("wheat")
        if "Alma" in crop_type or "Üzüm" in crop_type:  # Fruits
            default_expertise.append("orchard")
        
        # Auto-enable advanced tools for experts
        if experience == "expert":
            default_expertise.append("advanced")
    
    # Default to general if no specific expertise detected
    if not default_expertise:
        default_expertise = ["general"]
    
    # Load persisted overrides (user can change defaults)
    persisted = await load_user_settings(user)
    user_expertise = persisted.get("expertise_areas", default_expertise)
    
    settings = await cl.ChatSettings([
        # ... existing settings (language, currency, etc.) ...
        
        # NEW: Multi-select expertise areas
        MultiSelect(
            id="expertise_areas",
            label="🧠 Ekspertiza sahələri",
            values=[
                "general",    # Ümumi kənd təsərrüfatı
                "cotton",     # Pambıqçılıq
                "wheat",      # Taxılçılıq
                "orchard",    # Meyvəçilik
                "vegetable",  # Tərəvəz
                "livestock",  # Heyvandarlıq
                "advanced",   # Qabaqcıl texnologiyalar
            ],
            initial_values=user_expertise,  # Smart defaults!
            description="Hansı sahələrdə məsləhət almaq istəyirsiniz? (Birdən çox seçə bilərsiniz)",
        ),
    ]).send()
```

#### 2. Update Starters Based on Selected Expertise
```python
@cl.set_starters
async def set_starters(current_user: cl.User = None, chat_profile: str = None):
    """Generate starters based on user's selected expertise areas."""
    
    # Get user's expertise preferences from settings
    settings = cl.user_session.get("chat_settings", {})
    expertise_areas = settings.get("expertise_areas", ["general"])
    
    starters = []
    
    # Add starters for each selected expertise
    if "general" in expertise_areas:
        starters.extend([
            cl.Starter(label="📅 Həftəlik plan", message="Bu həftə üçün iş planı hazırla"),
            cl.Starter(label="🌤️ Hava proqnozu", message="Bu günkü hava proqnozu necədir?"),
        ])
    
    if "cotton" in expertise_areas:
        starters.extend([
            cl.Starter(label="🌱 Pambıq əkini", message="Pambıq əkini üçün ən yaxşı vaxt nədir?"),
            cl.Starter(label="🐛 Pambıq zərərvericisi", message="Pambıqda hansı zərərvericilər var?"),
        ])
    
    if "wheat" in expertise_areas:
        starters.extend([
            cl.Starter(label="🌾 Buğda əkini", message="Payızlıq buğda nə vaxt əkilir?"),
            cl.Starter(label="🌡️ Don zədəsi", message="Buğdanı dondan necə qorumaq olar?"),
        ])
    
    if "advanced" in expertise_areas:
        starters.extend([
            cl.Starter(label="📊 Torpaq analizi", message="Torpaq analizinin nəticələrini şərh et"),
            cl.Starter(label="🗺️ Peyk məlumatları", message="Sahəmin NDVI şəkillərini göstər"),
        ])
    
    # Return up to 6 most relevant starters
    return starters[:6]
```

#### 3. Update System Prompt Based on Combined Expertise
```python
@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming message with context-aware system prompt."""
    
    # Get user's expertise areas from settings
    settings = cl.user_session.get("chat_settings", {})
    expertise_areas = settings.get("expertise_areas", ["general"])
    
    # Build system prompt combining selected expertise
    system_prompt_parts = [BASE_SYSTEM_PROMPT]
    
    if "cotton" in expertise_areas:
        system_prompt_parts.append(COTTON_EXPERTISE_PROMPT)
    if "wheat" in expertise_areas:
        system_prompt_parts.append(WHEAT_EXPERTISE_PROMPT)
    if "advanced" in expertise_areas:
        system_prompt_parts.append(ADVANCED_EXPERTISE_PROMPT)
    
    system_prompt = "\n\n".join(system_prompt_parts)
    
    # Send to LangGraph with combined context
    ...
```

---

## 🎨 Benefits of This Approach

### 1. Aligns with EKTİS Reality
Real Azerbaijani farmers grow **multiple crops**:
- Cotton farmer in summer + Wheat in winter (crop rotation)
- Apple orchard + Beekeeping (synergy)
- Vegetable greenhouse + Livestock (integrated farm)

**Current problem:** Chat profiles force single-crop identity  
**Solution:** Multi-select allows "I need help with cotton AND wheat"

### 2. JIT Provisioning Intelligence
ALEM persona already knows user's context:
```python
# From database:
alem_persona.crop_type = "Pambıq"  # Cotton
alem_persona.experience_level = "expert"

# Smart defaults:
expertise_areas = ["cotton", "advanced"]  # Auto-enable!
```

**User sees:** "Oh, the system already knows I grow cotton! But I can add wheat too."

### 3. Unified Settings Experience
**Before:**
- Language/Currency/Detail Level → Chat Settings sidebar
- Expertise (Cotton/Wheat/Expert) → Top dropdown (separate!)

**After:**
- Language/Currency/Detail Level → Chat Settings
- Expertise Areas → **ALSO in Chat Settings** (all in one place!)

### 4. Persistence Across Sessions
Chat settings are **already persisted** to database:
```python
# data_layer.py
async def save_user_settings(user: cl.User, settings: dict):
    """Save settings to users.metadata JSONB column."""
    # expertise_areas stored alongside language, currency, etc.
```

**Benefit:** User selects "cotton + wheat" once, persisted forever.

### 5. Future: Link to Real Farm Data
When EKTİS integration is live:
```python
# Fetch real crops from user's parcels
async def get_user_crops_from_ektis(fin_code: str) -> list[str]:
    parcels = await ektis_api.get_farmer_parcels(fin_code)
    crops = set()
    for parcel in parcels:
        crop = parcel.current_crop  # From sowing_declarations
        if crop == "Pambıq":
            crops.add("cotton")
        elif crop in ["Qışlıq buğda", "Yazlıq buğda"]:
            crops.add("wheat")
    return list(crops)

# Auto-populate expertise_areas from REAL data
default_expertise = await get_user_crops_from_ektis(user.fin_code)
```

---

## 📋 Implementation Checklist

### Phase 1: Multi-Select in Settings (Week 1)
- [ ] Add `MultiSelect` widget to `setup_chat_settings()`
- [ ] Define expertise categories (cotton, wheat, orchard, vegetable, livestock, advanced)
- [ ] Implement smart defaults from ALEM persona
- [ ] Update `save_user_settings()` to persist `expertise_areas`

### Phase 2: Context-Aware Starters (Week 1)
- [ ] Update `@cl.set_starters` to read from `expertise_areas` setting
- [ ] Create starter pools for each expertise category
- [ ] Combine and return top 6 most relevant starters
- [ ] Test multi-select behavior (e.g., "cotton + wheat" shows both crop starters)

### Phase 3: Combined System Prompts (Week 2)
- [ ] Extract expertise-specific prompts to constants
- [ ] Build combined system prompt in `on_message()`
- [ ] Test combined expertise (e.g., cotton + advanced = cotton expert with GIS data)

### Phase 4: EKTİS Integration (Month 1)
- [ ] Fetch real crops from `sowing_declarations` table
- [ ] Map `CropType` enum to expertise categories
- [ ] Auto-populate `expertise_areas` from real farm data
- [ ] Allow user to override auto-detected crops

---

## 🎯 Migration Strategy: Backward Compatibility

### Option A: Keep Both (Gradual Migration)
Keep existing top dropdown for now, add new multi-select to settings:
- Users who don't change settings → Top dropdown still works
- Users who configure settings → Multi-select takes precedence

### Option B: Full Migration (Cleaner UX)
Remove top dropdown completely, move everything to settings:
- Explain change in welcome message: "Configure expertise in settings!"
- Provide migration guide for existing users

**Recommendation:** Option B (full migration) for cleaner UX.

---

## 🔍 Code Comparison: Before vs After

### Before (Single-Select Dropdown):
```python
@cl.set_chat_profiles
async def chat_profiles():
    return [
        cl.ChatProfile(name="general", ...),
        cl.ChatProfile(name="cotton", ...),
        cl.ChatProfile(name="wheat", ...),
    ]

# User must manually select ONE profile
# No smart defaults
# Not persisted across sessions
```

### After (Multi-Select in Settings):
```python
@cl.on_chat_start
async def setup_chat_settings():
    # Smart defaults from ALEM persona
    default_expertise = detect_from_persona(alem_persona)
    
    MultiSelect(
        id="expertise_areas",
        values=["general", "cotton", "wheat", "orchard", "advanced"],
        initial_values=default_expertise,  # Auto-configured!
    )

# User can select MULTIPLE areas
# Smart defaults from persona
# Persisted in database across sessions
```

---

## 🧪 Test Scenarios

### Scenario 1: New Cotton Farmer
```python
# ALEM persona:
crop_type = "Pambıq"
experience_level = "novice"

# Auto-detected expertise:
expertise_areas = ["general", "cotton"]

# Starters shown:
# - 📅 Həftəlik plan (general)
# - 🌤️ Hava proqnozu (general)
# - 🌱 Pambıq əkini (cotton)
# - 🐛 Pambıq zərərvericisi (cotton)
```

### Scenario 2: Experienced Multi-Crop Farmer
```python
# ALEM persona:
crop_type = "Pambıq, Buğda"  # Multi-crop!
experience_level = "expert"

# Auto-detected expertise:
expertise_areas = ["cotton", "wheat", "advanced"]

# Starters shown:
# - 🌱 Pambıq əkini (cotton)
# - 🌾 Buğda əkini (wheat)
# - 📊 Torpaq analizi (advanced)
# - 🗺️ Peyk məlumatları (advanced)
```

### Scenario 3: User Override
```python
# Auto-detected:
expertise_areas = ["cotton"]

# User manually adds:
expertise_areas = ["cotton", "orchard", "advanced"]
# Reason: Planning to expand into apple orchard

# System respects user's choice, persists to database
```

---

## 💡 Future Enhancements

### 1. Weighted Expertise (Priority System)
```python
MultiSelect(
    id="expertise_areas",
    values=[
        {"value": "cotton", "weight": 0.7},  # 70% of farm
        {"value": "wheat", "weight": 0.2},   # 20% of farm
        {"value": "orchard", "weight": 0.1}, # 10% of farm
    ],
)

# Starters weighted by crop percentage:
# - 4 cotton starters (70%)
# - 1 wheat starter (20%)
# - 1 orchard starter (10%)
```

### 2. Seasonal Expertise
```python
# Winter: wheat/barley expertise more relevant
# Summer: cotton/vegetable expertise more relevant

if current_month in [11, 12, 1, 2]:  # Winter
    default_expertise.append("wheat")
elif current_month in [4, 5, 6, 7]:  # Summer
    default_expertise.append("cotton")
```

### 3. Learning from Usage
```python
# Track which expertise areas user asks about most
# Auto-adjust defaults over time

usage_stats = {
    "cotton": 45,  # 45 questions about cotton
    "wheat": 12,   # 12 questions about wheat
    "advanced": 3, # 3 questions about GIS/sensors
}

# Suggest adding "cotton" to expertise if not already there
```

---

## 🏆 Conclusion

### Issue 1: Alembic Command
**Solution:** Activate virtual environment first:
```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

### Issue 2: Chat Profiles UX
**Your insight is correct!** Moving to multi-select chat settings:
- ✅ Aligns with real multi-crop farming
- ✅ Smart defaults from ALEM persona
- ✅ Persisted across sessions
- ✅ Unified settings experience
- ✅ Prepares for EKTİS integration

**Recommendation:** Implement Phase 1 (multi-select in settings) this week. This is a **high-impact UX improvement** that makes the system feel genuinely intelligent.

---

**Next Steps:**
1. Run migration: `.\.venv\Scripts\Activate.ps1; alembic upgrade head`
2. Implement multi-select expertise in chat settings
3. Update starters to be context-aware
4. Test with different ALEM personas
