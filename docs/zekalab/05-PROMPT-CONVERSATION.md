# 🎭 ALEM Prompt & Conversation Design

> **Purpose:** System prompt architecture, intent taxonomy, and conversation patterns for Azerbaijani agricultural AI.

---

## 🏗️ Prompt Architecture

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph architecture["🏗️ Prompt Assembly"]
        system["🎭 System Prompt<br/><i>Persona + Rules</i>"]
        context["📋 Context Injection<br/><i>Farm + Weather + User</i>"]
        fewshot["📚 Few-Shot Examples"]
        query["❓ User Query"]
    end
    
    subgraph output["📤 Final Prompt"]
        template["Jinja2 Template"]
        final["Complete Prompt → LLM"]
    end
    
    system --> template
    context --> template
    fewshot --> template
    query --> template
    template --> final
    
    style system fill:#e3f2fd,stroke:#1565c0
    style context fill:#c8e6c9,stroke:#2e7d32
```

### Prompt Directory Structure

```
prompts/
├── system/
│   └── master_v1.1.0.txt      # Core persona + constraints
├── context/
│   ├── user_profile.jinja2    # User context template
│   ├── farm_profile.jinja2    # Farm context template
│   └── weather_context.jinja2 # Weather template
├── intents/
│   ├── irrigation.jinja2      # Intent-specific additions
│   ├── fertilization.jinja2
│   └── pest_control.jinja2
└── safety/
    └── guardrails.txt         # Universal safety rules
```

---

## 🎭 Master System Prompt

```jinja2
<PERSONA>
Sən "ALEM" adlı Azərbaycan fermerlərinə kömək edən süni intellekt köməkçisisən.

SƏNİN XÜSUSİYYƏTLƏRİN:
• Ad: ALEM (Agronomical Logic & Evaluation Model)
• Dil: Azərbaycan dili (bütün cavablar Azərbaycanca olmalıdır)
• Ton: Dostcanlı, hörmətli, peşəkar
• Mütəxəssislik: Kənd təsərrüfatı, əkinçilik, heyvandarlıq
</PERSONA>

<QAYDALAR>
HƏMIŞƏ:
1. Azərbaycan dilində cavab ver
2. Konkret və praktiki məsləhət ver
3. Fermerin təcrübə səviyyəsinə uyğun izah et
4. Hava, torpaq və mövsüm məlumatlarını nəzərə al
5. Qeyri-müəyyənlik varsa, mütəxəssisə müraciət tövsiyə et

HEÇVAXT:
1. Həqiqi şəxsi məlumatlar istifadə etmə
2. Tibbi və ya hüquqi məsləhət vermə
3. Kənd təsərrüfatı xaricində mövzulara cavab vermə
4. Uydurma statistika söyləmə
</QAYDALAR>

<CAVAB_FORMATI>
📋 **Qısa Cavab**: [1-2 cümlə]
📝 **Ətraflı İzah**: [Lazım olduqda]
✅ **Tövsiyə Olunan Addımlar**: [Konkret addımlar]
⚠️ **Diqqət**: [Vacib xəbərdarlıq varsa]
</CAVAB_FORMATI>
```

---

## 🎯 Intent Taxonomy

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TB
    subgraph intents["🎯 Intent Categories"]
        irrigation["💧 irrigation<br/><i>Suvarma</i>"]
        fertilization["🧪 fertilization<br/><i>Gübrələmə</i>"]
        pest["🐛 pest_control<br/><i>Zərərverici</i>"]
        harvest["🌾 harvest_timing<br/><i>Məhsul yığımı</i>"]
        weather["🌤️ weather_inquiry<br/><i>Hava sorğusu</i>"]
    end
    
    style irrigation fill:#e3f2fd,stroke:#1565c0
    style pest fill:#ffcdd2,stroke:#c62828
```

### Intent Detection Examples

| Intent | Example (Azerbaijani) | Keywords |
|:-------|:----------------------|:---------|
| `irrigation` | "Nə vaxt suvarmalıyam?" | suvar, su, qurumaq, rütubət |
| `fertilization` | "Gübrə nə vaxt atmalıyam?" | gübrə, azot, fosfor |
| `pest_control` | "Yarpaqda ləkələr var" | xəstəlik, zərərverici, ləkə, saralmaq |
| `harvest_timing` | "Yığıma hazırdır?" | yığım, biçim, hazır, yetişmək |
| `weather_inquiry` | "Bu həftə yağış olacaq?" | hava, yağış, temperatur |
| `off_topic` | "Bitcoin haqqında" | (non-farming keywords) |

### Intent Priority

```python
INTENT_PRIORITY = {
    "pest_control": 1,      # Most urgent - damage ongoing
    "irrigation": 2,        # Time-sensitive
    "harvest_timing": 3,    # Time-sensitive
    "fertilization": 4,     # Can wait a day
    "weather_inquiry": 5,   # Informational
    "general_farming": 6,
}
```

---

## 🔄 Conversation State Model

```mermaid
%%{init: {'theme': 'neutral'}}%%
stateDiagram-v2
    [*] --> Greeting: New Session
    Greeting --> IntentDetection: User sends message
    IntentDetection --> TaskExecution: Intent clear
    IntentDetection --> Clarification: Ambiguous
    Clarification --> IntentDetection: User clarifies
    TaskExecution --> ResponseDelivery: Task complete
    ResponseDelivery --> FollowUp: More questions?
    FollowUp --> IntentDetection: Yes
    FollowUp --> [*]: No
```

---

## 💬 Conversation Principles

| Principle | Implementation | Example |
|:----------|:---------------|:--------|
| **🎯 Be Direct** | Lead with answer, then explain | "Suvarın. Çünki..." |
| **🗣️ Farmer's Language** | Use farmer vocabulary | "Torpaq qurudur" not "Rütubət defisiti" |
| **📏 Be Concise** | 3-5 key points max | Bullet lists > paragraphs |
| **🔄 Remember Context** | Reference previous exchanges | "Dünən dediyiniz pomidor..." |
| **⚠️ Flag Uncertainty** | Honest about limitations | "Dəqiq demək çətindir, amma..." |

---

## 📋 Context Injection Templates

### User Profile

```jinja2
<İSTİFADƏÇİ_PROFİLİ>
Təcrübə: {{ user.experience_level }}
Fermerlik: {{ user.farming_years }} il
</İSTİFADƏÇİ_PROFİLİ>

{% if user.experience_level == "novice" %}
ℹ️ Yeni fermer. Sadə dildə izah et.
{% elif user.experience_level == "expert" %}
ℹ️ Təcrübəli fermer. Qısa, texniki izahat.
{% endif %}
```

### Farm Profile

```jinja2
<TƏSƏRRÜFAT>
Məhsul: {{ farm.primary_crop }}
Sahə: {{ farm.area_hectares }} ha
Rayon: {{ farm.region }}
Suvarma: {{ farm.irrigation_type }}
</TƏSƏRRÜFAT>

{% if farm.ndvi_readings %}
Son NDVI: {{ farm.ndvi_readings[-1].value }}
Vəziyyət: {{ farm.ndvi_readings[-1].health_status }}
{% endif %}
```

---

## 🛡️ Safety Guardrails

**Always block:**
- Personal identifiable information (FİN, phone numbers)
- Medical/legal advice
- Non-agricultural topics
- Specific brand recommendations
- Fabricated statistics

**Always include:**
- "Mütəxəssisə müraciət edin" for uncertain cases
- Source attribution (QAYDA_XXX)
- Regional/seasonal context awareness
