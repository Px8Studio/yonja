# Yonca Mobile App Features → Chainlit UI Replication

**Status:** ✅ Implemented
**Date:** 2026-01-21
**Integration Level:** Chat Settings + Agent Context + Planning System

---

## Overview

This document describes the replication of Yonca Mobile App's user profile and planning features in the Chainlit UI. The mobile app captures detailed farm profiles and generates month-by-month action plans based on crop/region combinations. We've replicated these capabilities in chat settings to provide feature parity.

---

## Mobile App Analysis

### User Groups Identified by Mobile App

Based on the mobile app screenshots, Yonca Mobile identifies farmers by:

1. **Primary Crop** - Main agricultural product (Cotton, Wheat, Apple, etc.)
2. **Region** - Geographic/economic zone (Aran, Quba-Xaçmaz, Lənkəran, etc.)
3. **Farm Size** - Land area in hectares
4. **Experience Level** - Farming expertise (Novice, Intermediate, Expert)
5. **Soil Type** - Primary soil characteristics (Clay, Sandy, Loam, Saline)
6. **Irrigation System** - Water delivery method (Drip, Pivot, Flood, Rainfed)

### Planning Features

The mobile app's **Planner** module:
- Accepts crop + region + month combination
- Generates month-by-month action insights
- Provides category-specific recommendations:
  - Planting schedules
  - Irrigation timing
  - Fertilization plans
  - Pest control measures
  - Harvest preparation
  - Soil management
  - Pruning activities
  - Weather monitoring

---

## Chainlit Implementation

### Chat Settings Structure

**Location:** `demo-ui/app.py` → `setup_chat_settings()`

```python
# FARM PROFILE SECTION
Select(id="crop_type", label="Əsas məhsul / Primary Crop")
Select(id="region", label="Region")
NumberInput(id="farm_size_ha", label="Sahə (hektar) / Farm Size (ha)")
Select(id="experience_level", label="Təcrübə səviyyəsi / Experience Level")
Select(id="soil_type", label="Torpaq növü / Soil Type")
Select(id="irrigation_type", label="Suvarma sistemi / Irrigation System")

# PLANNING & ACTIONS SECTION
Select(id="planning_month", label="Planlaşdırma ayı / Planning Month")
MultiSelect(id="action_categories", label="Fəaliyyət kateqoriyaları / Action Categories")

# EXPERTISE AREAS (Pre-existing)
MultiSelect(id="expertise_areas", label="Ekspertiza sahələri / Expertise Areas")

# UI PREFERENCES (Pre-existing)
Select(id="language")
Select(id="currency")
Select(id="detail_level")
Select(id="units")
Switch(id="notifications")
Switch(id="show_sources")
```

### Design Decisions

#### No Emojis in Chat Settings
- **Requirement:** User explicitly requested "no emojis in chatsettings ui please!"
- **Implementation:** Removed emoji prefixes from all setting labels
- **Reason:** Mobile app uses clean, professional UI without decorative icons

#### Bilingual Labels
- All settings use format: `"Azərbaycanca / English"`
- Supports primary user base (Azerbaijani farmers) while maintaining accessibility
- Example: `"Pambıq (Cotton)"`, `"Yanvar / January"`

#### Smart Defaults
- Crop type initialized from ALEM persona's `crop_type`
- Experience level mapped from persona's `experience_level`
- Farm size pulled from persona's `farm_size_ha`
- Planning month defaults to current month (January)
- Action categories pre-select common tasks (Planting, Irrigation, Fertilization)

---

## Settings Handler Integration

### `@on_settings_update` Handler

**Location:** `demo-ui/app.py` (Lines 1344-1520)

**Responsibilities:**
1. **Parse Farm Profile Fields**
   - Extract crop, region, size, experience from bilingual values
   - Normalize Azerbaijani experience levels to English keys
   - Clean soil/irrigation types for internal use

2. **Build Enhanced System Prompt**
   - Inject farm profile context into agent instructions
   - Combine with expertise-based prompts
   - Example:
     ```
     FARM PROFILE:
     - Primary Crop: Pambıq
     - Region: Aran
     - Farm Size: 45.3 ha
     - Experience: expert
     - Soil Type: Lopam
     - Irrigation: Damcı
     ```

3. **Trigger Planning Logic**
   - Log planning requests with month + categories
   - **(TODO)** Integrate with rules engine for monthly action generation

4. **Persist Settings**
   - Save to database for authenticated users
   - Maintain across sessions

5. **User Feedback**
   - Send confirmation message with farm summary
   - Format: `"Pambıq • Aran • 45.3 ha"`
   - Include planning context if categories selected

---

## System Prompt Enhancement

### Before (Expertise Only)
```python
combined_prompt = build_combined_system_prompt(expertise_ids)
```

### After (Expertise + Farm Profile)
```python
combined_prompt = build_combined_system_prompt(expertise_ids)

farm_context = f"""

FARM PROFILE:
- Primary Crop: {crop_type}
- Region: {region}
- Farm Size: {farm_size_ha} ha
- Experience: {experience_level}
- Soil Type: {soil_type}
- Irrigation: {irrigation_type}

When providing recommendations, consider these farm-specific details.
"""

combined_prompt += farm_context
```

**Impact:** Agent now provides contextually relevant advice based on farmer's actual conditions (e.g., drip irrigation recommendations for water-scarce regions, expert-level deep dives for experienced farmers).

---

## Planning System Integration

### Current Status
- ✅ Settings capture planning month + action categories
- ✅ Logging infrastructure in place
- ⏳ Rules engine integration pending

### Planned Integration

**Rules Engine Connection:**
```python
if action_categories:
    # Generate monthly plan using rules engine
    from yonca.rules_engine import generate_monthly_plan

    plan = await generate_monthly_plan(
        crop=crop_type,
        region=region,
        month=planning_month,
        categories=action_categories,
        soil_type=soil_type,
        irrigation_type=irrigation_type,
    )

    # Display plan in chat or dashboard
    await send_monthly_plan_message(plan)
```

**Rules Engine Requirements:**
- Accept farm profile parameters
- Return structured action plan with:
  - Week-by-week tasks
  - Priority levels (Critical, Important, Optional)
  - Resource requirements (water, fertilizer, labor)
  - Weather dependencies
  - Best practices for crop/region

---

## Data Flow

```
User selects settings
        ↓
@on_settings_update triggered
        ↓
Parse bilingual values → Normalize to clean keys
        ↓
Build enhanced system prompt (expertise + farm profile)
        ↓
Save to session + database (if authenticated)
        ↓
(Future) Trigger rules engine for monthly planning
        ↓
Agent uses farm context in all responses
```

---

## Field Mappings

### Crop Types (12 options)
```
Pambıq (Cotton), Buğda (Wheat), Arpa (Barley), Qarğıdalı (Corn),
Alma (Apple), Üzüm (Grape), Fındıq (Hazelnut),
Pomidor (Tomato), Xıyar (Cucumber), Bibər (Pepper),
Çay (Tea), Sitrus (Citrus)
```

### Regions (8 economic zones)
```
Aran, Quba-Xaçmaz, Şəki-Zaqatala, Mil-Muğan,
Lənkəran-Astara, Gəncə-Qazax, Naxçıvan, Qarabağ
```

### Experience Levels
```
Başlanğıc / Novice → "novice"
Orta / Intermediate → "intermediate"
Mütəxəssis / Expert → "expert"
```

### Soil Types
```
Gilli / Clay, Qumlu / Sandy, Lopam / Loam, Şoranlı / Saline
```

### Irrigation Systems
```
Damcı / Drip, Pivot, Şırım / Flood, Yağış / Rainfed
```

### Planning Months
```
Yanvar through Dekabr (all 12 months, bilingual)
```

### Action Categories (8 categories)
```
Əkin / Planting
Suvarma / Irrigation
Gübrələmə / Fertilization
Zərərverici mübarizə / Pest Control
Məhsul yığımı / Harvest
Torpaq işləri / Soil Work
Budama / Pruning
İqlim monitorinqi / Weather Monitoring
```

---

## Testing Strategy

### Manual Testing
1. Open chat settings sidebar
2. Select farm profile values (crop, region, size, etc.)
3. Choose planning month + action categories
4. Verify settings update message shows farm summary
5. Ask agent a farming question → confirm response uses farm context

### Example Test Case
```
Settings:
- Crop: Pambıq (Cotton)
- Region: Aran
- Size: 10 ha
- Experience: Intermediate
- Planning Month: May
- Actions: [Irrigation, Fertilization]

User Query: "When should I water my cotton?"

Expected Response:
- Mentions Aran region climate
- References 10 ha scale requirements
- Suggests intermediate-level practices
- Provides May-specific irrigation timing
```

---

## Comparison: Mobile vs. Chainlit

| Feature | Mobile App | Chainlit UI | Status |
|---------|-----------|-------------|--------|
| Crop selection | ✅ | ✅ | Complete |
| Region selection | ✅ | ✅ | Complete |
| Farm size input | ✅ | ✅ | Complete |
| Experience level | ✅ | ✅ | Complete |
| Soil type | ✅ | ✅ | Complete |
| Irrigation type | ✅ | ✅ | Complete |
| Month selection | ✅ | ✅ | Complete |
| Action categories | ✅ | ✅ | Complete |
| Agent context injection | ✅ | ✅ | Complete |
| Monthly plan generation | ✅ | ⏳ | Pending rules engine |
| Settings persistence | ✅ | ✅ | Complete |

---

## Next Steps

### P1: Rules Engine Integration
- [ ] Connect planning fields to rules engine
- [ ] Generate month-by-month action plans
- [ ] Display plans in chat or dedicated dashboard section
- [ ] Add "View My Plan" action button

### P2: Enhanced Planning UI
- [ ] Add calendar view for annual planning
- [ ] Visualize critical action periods
- [ ] Export plans to PDF/CSV

### P3: Mobile-Web Sync (Future)
- [ ] Shared user profile between mobile + web
- [ ] Cross-platform settings sync
- [ ] Unified planning state

---

## Technical Notes

### Why `NumberInput` for Farm Size?
- Allows flexible precision (0.5 ha increments)
- Supports wide range (0.5 ha to 500 ha)
- Better UX than text input for numeric values

### Why Multi-Select for Action Categories?
- Users often need multiple action types simultaneously
- Example: May requires both irrigation + fertilization
- Single-select would force multiple setting updates

### Normalization Logic
All bilingual values are split on `"/"` or `"("` to extract clean keys for internal logic:
```python
"Pambıq (Cotton)" → "Pambıq"
"Yanvar / January" → "January"
"Orta / Intermediate" → "orta" → "intermediate"
```

---

## Related Documentation

- [11-CHAINLIT-UI.md](./11-CHAINLIT-UI.md) - Chainlit integration guide
- [00-IMPLEMENTATION-BACKLOG.md](./00-IMPLEMENTATION-BACKLOG.md) - Project roadmap
- [02-SYNTHETIC-DATA-ENGINE.md](./02-SYNTHETIC-DATA-ENGINE.md) - User profile schemas
- `src/yonca/agent/state.py` - Agent state management
- `demo-ui/app.py` - Main application file

---

**Conclusion:** Yonca Chainlit UI now has feature parity with mobile app's user profile and planning interface. Farmers can configure detailed farm profiles, select planning parameters, and receive contextually relevant advice. The pending rules engine integration will complete the planning feature by generating actionable month-by-month insights.
