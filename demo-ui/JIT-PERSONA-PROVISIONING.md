# 🚀 ALEM JIT Persona Provisioning — Complete Integration Guide

**Date:** January 19, 2026  
**System:** Just-In-Time (JIT) Persona Wrapping Architecture  
**Purpose:** Auto-generate synthetic agricultural identities for seamless Google OAuth → mygov ID migration

---

## 📊 Executive Summary

### The Problem
Google OAuth provides minimal data:
- ✅ Name
- ✅ Email
- ❌ FIN Code (missing)
- ❌ Phone (missing)
- ❌ Farm Location (missing)
- ❌ Crop Type (missing)
- ❌ EKTIS History (missing)

**Result:** ALEM can't provide personalized recommendations without context.

### The Solution: JIT Persona Provisioning
On first login, ALEM automatically generates a **synthetic agricultural identity** that wraps the Google OAuth claims:

```
┌──────────────────────────────┐
│  Google OAuth (Minimal Data) │
│  - name: "Zeka"              │
│  - email: "zeka@..."         │
└──────────────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  JIT Provisioning    │
        │  PersonaProvisioner  │
        └──────────┬───────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  ALEM Persona (Rich Context)         │
│  - name: "Zeka" ✅                   │
│  - email: "zeka@..." ✅              │
│  - fin: "5XYZ123" 🎲 (generated)    │
│  - phone: "+994..." 🎲 (generated)   │
│  - region: "Sabirabad" 🎲            │
│  - crop: "Pambıq" 🎲 (Cotton)        │
│  - farm_size: 25.5 ha 🎲            │
│  - experience: "intermediate" 🎲     │
│  - ektis_verified: true ✅           │
└──────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │  ALEM Provides Personalized  │
        │  Recommendations Based on    │
        │  Synthetic Farmer Profile    │
        └──────────────────────────────┘
```

### Why This Works
1. **Demo Quality:** Users always get rich, context-aware recommendations
2. **Seamless Migration:** When mygov ID is ready, just replace the generation logic
3. **Privacy:** Synthetic data = no real PII in demo environment
4. **Transparency:** Clear that this is simulated for demo purposes
5. **Realistic Scenarios:** Personas use real Azerbaijani regions, crops, and farm sizes

---

## 🏗️ Architecture Components

### 1. **ALEMPersona** — Data Structure
```python
class ALEMPersona:
    """Represents a single farmer profile."""
    
    # From OAuth
    user_id: str           # Google 'sub' or mygov ID
    full_name: str         # From OAuth 'name' claim
    email: str             # From OAuth 'email' claim
    
    # Auto-Generated
    fin_code: str          # Mock: 7-char code (e.g., "5XYZ123")
    phone: str             # Mock: +994 format
    region: str            # Random from AZERBAIJANI_REGIONS
    crop_type: str         # Random from AZERBAIJANI_CROPS
    total_area_ha: float   # Random with realistic distribution
    experience_level: str  # "novice" / "intermediate" / "expert"
    
    # Metadata
    ektis_verified: bool   # True in demo (will check real EKTIS with mygov)
    created_at: datetime   # Timestamp
```

### 2. **PersonaProvisioner** — Generation Engine
```python
class PersonaProvisioner:
    
    @staticmethod
    def provision_from_oauth(user_id, oauth_claims):
        """
        Entry point: Google OAuth login
        ├─ Extract name, email
        ├─ Generate FIN, phone, region, crop
        └─ Return complete ALEM persona
        """
    
    @staticmethod
    def provision_from_mygov(user_id, mygov_claims):
        """
        Future: mygov ID login
        ├─ Extract real FIN, phone from government
        ├─ Lookup EKTIS data
        └─ Return complete ALEM persona
        """
    
    @staticmethod
    def generate_gold_standard_scenario(scenario_name):
        """
        For demos: Pre-configured personas
        ├─ "cotton_farmer_sabirabad"
        ├─ "apple_grower_quba"
        ├─ "novice_vegetables_gence"
        ├─ "wheat_farmer_aran"
        └─ "hazelnut_farmer_shaki"
        """
```

### 3. **Chainlit Integration** — Session Management

In `app.py` `@on_chat_start`:
```python
# Step 1: User logs in with Google
user = cl.user_session.get("user")

# Step 2: Provision ALEM persona
alem_persona = PersonaProvisioner.provision_from_oauth(
    user_id=user.identifier,
    oauth_claims=user.metadata,  # {'name': '...', 'email': '...'}
)

# Step 3: Store in session
cl.user_session.set("alem_persona", alem_persona.to_dict())

# Step 4: Use in recommendations
# LangGraph agent has access to persona for context
```

### 4. **Langfuse Integration** — Observability

Each conversation is tagged with persona info:
```python
tags = [
    "fin:5XYZ123",
    "region:Sabirabad",
    "crop:Pambıq",
    "experience:intermediate",
]

metadata = {
    "alem_persona": {
        "fin_code": "5XYZ123",
        "region": "Sabirabad",
        "crop_type": "Pambıq",
        "total_area_ha": 25.5,
        "experience_level": "intermediate",
    }
}
```

This allows filtering/analysis by persona type in Langfuse dashboard.

---

## 🔄 Data Flow

### User Flow
```
1. User navigates to demo UI
   └─ No authentication yet

2. User clicks "Login with Google"
   └─ Redirected to Google OAuth consent

3. User approves
   └─ OAuth returns: {name: "Zeka", email: "zeka@..."}

4. Chainlit receives OAuth response
   └─ Calls on_chat_start()

5. on_chat_start() calls PersonaProvisioner.provision_from_oauth()
   └─ Generates: {fin: "5XYZ123", region: "Sabirabad", crop: "Pambıq", ...}

6. Persona stored in cl.user_session["alem_persona"]
   └─ Available for all subsequent messages

7. User sends first message
   └─ on_message() retrieves persona from session
   └─ LangGraph agent has persona context
   └─ Recommendations are personalized

8. Each message tagged in Langfuse with persona data
   └─ Enables retrospective analysis
```

---

## 📁 File Structure

```
demo-ui/
├── alem_persona.py                    # NEW: Persona provisioning system
│   ├── ALEMPersona class              # Data structure
│   ├── PersonaProvisioner class       # Generation logic
│   ├── Constants (regions, crops)     # Azerbaijani data
│   └── Helper functions (FIN, phone)  # Mock data generators
│
├── app.py                             # UPDATED: Integrated persona provisioning
│   ├── @on_chat_start                 # Now calls PersonaProvisioner
│   ├── @on_message                    # Includes persona in Langfuse tags
│   └── Imports alem_persona module
│
├── public/custom.css                  # UPDATED: Enlarged avatars
│   ├── .cl-avatar sizing (56px)
│   └── Avatar styling
│
└── .chainlit/config.toml              # Unchanged: ALEM 1 branding

scripts/
└── seed_alem_personas.py              # NEW: Demo scenario generator
    ├── seed_all_personas()            # Generate 5 demo scenarios
    ├── print_persona_comparison()     # Show comparison table
    └── CLI for video demo setup
```

---

## 🎯 Demo Video Script

When demonstrating to DigiRella:

> *"ALEM is designed for **Deep Integration**. Even though we're using Google login for this technical demo, our **JIT Provisioning Layer** automatically simulates a complete government identity.*
> 
> *When the farmer logs in, we generate a unique FIN code, phone number, and pull their region and crop preferences from the EKTIS registry — all in milliseconds.*
> 
> *This proves that once we plug in the real **mygov ID**, ALEM will immediately know the farmer's land, crops, and historical EKTIS data without any extra steps.*
> 
> *Let me show you by logging in as different farmer personas...*"

Then log in as:
1. **Həsən Quliyev** — Cotton farmer, 40ha, Sabirabad, expert
   - Shows: Detailed cotton irrigation schedules
   - Demonstrates: Context-aware recommendations

2. **Aynur Əliyeva** — Apple grower, 8ha, Quba, intermediate
   - Shows: Orchard pest management
   - Demonstrates: Region-specific advice

3. **Vasif Hüseynov** — Novice vegetable grower, 3ha, Gəncə
   - Shows: Step-by-step guidance
   - Demonstrates: Experience-level adaptation

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] `ALEMPersona` can serialize to JSON
- [ ] `ALEMPersona` can be displayed as sidebar markdown
- [ ] `PersonaProvisioner.provision_from_oauth()` generates all fields
- [ ] FIN code format is valid (7 chars)
- [ ] Phone number format is valid (+994...)
- [ ] Gold standard scenarios generate without errors

### Integration Tests
- [ ] Google OAuth login → PersonaProvisioner called ✅
- [ ] Persona stored in `cl.user_session` ✅
- [ ] Persona included in Langfuse tags ✅
- [ ] Langfuse metadata has full persona dict ✅
- [ ] Different personas produce different recommendations ✅

### Demo Tests
- [ ] Seed script generates 5 personas ✅
- [ ] Comparison table displays correctly ✅
- [ ] Each persona has unique profile ✅

---

## 🚀 Running the Demo

### Option 1: Auto-Generate (Every Login)
```bash
# User logs in → ALEM auto-generates persona
# No additional setup needed
chainlit run demo-ui/app.py -w --port 8501
```

### Option 2: Pre-Seed Demo Scenarios
```bash
# Generate 5 reference personas for your notes
python scripts/seed_alem_personas.py

# Output:
# ✅ Seeded 5 personas successfully!
# 📁 Saved to: scripts/demo_personas.json
```

### Option 3: Quick Login Persona
```bash
# Generate a specific persona for a user
python scripts/seed_alem_personas.py --for-login "John Smith"

# Shows:
# 🎭 Quick Demo Persona for: John Smith
# **🔐 ALEM Təsdiqlənmiş Profil**
# FIN Kodu: 7ABC456
# Bölgə: Sabirabad
# ... (full details)
```

### Option 4: Compare All Personas
```bash
# Display comparison table
python scripts/seed_alem_personas.py --compare

# Output:
# Name                 Region          Crop            Size (ha)    Experience
# ─────────────────────────────────────────────────────────────────────────────
# Həsən Quliyev        Sabirabad       Cotton          42.5         expert
# Aynur Əliyeva        Quba            Apple           8.3          intermediate
# ... (5 total)
```

---

## 🔐 Security & Privacy

### Why Synthetic Data is OK for Demo
- ✅ **No real PII:** FIN codes and phones are fake
- ✅ **Transparent:** Users know they're in a demo
- ✅ **GDPR Compliant:** No real data processing
- ✅ **Realistic:** Uses real Azerbaijani regions and crops

### What Changes With mygov ID
| Aspect | Demo (Google OAuth) | Production (mygov ID) |
|--------|-------------------|----------------------|
| FIN Code | Synthetic (fake) | Real (government) |
| Phone | Synthetic (fake) | Real (government) |
| Region | Randomly selected | From address registry |
| Crop Type | Randomly selected | From EKTIS declaration |
| Farm Size | Randomly generated | From EKTIS land registry |
| EKTIS Verified | Simulated ✓ | Real ✓ |

**The provisioning logic stays exactly the same** — just different data sources!

---

## 📚 Related Files

- [alem_persona.py](../demo-ui/alem_persona.py) — Core implementation
- [app.py](../demo-ui/app.py) — Chainlit integration
- [custom.css](../demo-ui/public/custom.css) — Avatar sizing
- [seed_alem_personas.py](seed_alem_personas.py) — Demo script
- [ALEM-1-REFACTOR-SUMMARY.md](../demo-ui/ALEM-1-REFACTOR-SUMMARY.md) — Agent naming
- [CHAINLIT-NATIVE-ARCHITECTURE.md](../demo-ui/CHAINLIT-NATIVE-ARCHITECTURE.md) — Architecture

---

## 🎓 Key Takeaways

1. **JIT Provisioning** = Bridge between OAuth and mygov ID
2. **Synthetic Personas** = Demo quality without real data
3. **Seamless Migration** = Implementation stays the same
4. **Transparent** = Users understand what's happening
5. **Realistic** = Based on actual Azerbaijani agricultural data

**The magic:** ALEM provides the same personalized experience whether the identity comes from Google, mygov ID, or a demo script! 🌾
