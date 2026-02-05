from alim.config import AgentMode

LLM_MODEL_PROFILES = {
    AgentMode.FAST.value: {
        "name": "Fast",
        "description": "**Fast** — Speed only. No tools/connectors.",
        "icon": "⚡",
    },
    AgentMode.THINKING.value: {
        "name": "Thinking",
        "description": "**Thinking** — Reasoning-heavy. No tools/connectors.",
        "icon": "🧠",
    },
    AgentMode.AGENT.value: {
        "name": "Agent",
        "description": "**Agent** — Full autonomy + MCP tools/connectors.",
        "icon": "🤖",
    },
}

EXPERTISE_AREAS = {
    "general": "Ümumi kənd təsərrüfatı",
    "cotton": "Pambıqçılıq",
    "wheat": "Taxılçılıq (buğda, arpa)",
    "orchard": "Meyvəçilik (alma, üzüm)",
    "vegetable": "Tərəvəzçilik",
    "livestock": "Heyvandarlıq",
    "advanced": "Qabaqcıl texnologiyalar",
}

CROP_TO_EXPERTISE = {
    # Industrial crops
    "Pambıq": ["cotton"],
    "Cotton": ["cotton"],
    # Grains
    "Buğda": ["wheat"],
    "Wheat": ["wheat"],
    "Arpa": ["wheat"],
    "Barley": ["wheat"],
    "Qarğıdalı": ["wheat"],  # Corn grouped with grains
    "Corn": ["wheat"],
    # Fruits/Orchards
    "Alma": ["orchard"],
    "Apple": ["orchard"],
    "Üzüm": ["orchard"],
    "Grape": ["orchard"],
    "Fındıq": ["orchard"],
    "Hazelnut": ["orchard"],
    "Nar": ["orchard"],
    "Pomegranate": ["orchard"],
    "Şaftalı": ["orchard"],
    "Peach": ["orchard"],
    # Vegetables
    "Pomidor": ["vegetable"],
    "Tomato": ["vegetable"],
    "Xıyar": ["vegetable"],
    "Cucumber": ["vegetable"],
    "Bibər": ["vegetable"],
    "Pepper": ["vegetable"],
    "Kartof": ["vegetable"],
    "Potato": ["vegetable"],
    # Specialty
    "Çay": ["vegetable"],  # Tea grouped with vegetables for now
    "Tea": ["vegetable"],
    "Sitrus": ["orchard"],
    "Citrus": ["orchard"],
}

EXPERIENCE_TO_EXPERTISE = {
    "expert": ["advanced"],
    "intermediate": [],
    "novice": [],
}

PROFILE_PROMPTS = {
    "general": "",  # Use default system prompt
    "cotton": """
Sən pambıqçılıq üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda pambıq becərmə (Aran bölgəsi, Muğan düzü) haqqında dərin biliyə maliksən.
Pambığın vegetasiya mərhələləri, suvarma rejimi, gübrələmə normaları və zərərvericilərə qarşı mübarizə haqqında ətraflı məlumat ver.
""",
    "wheat": """
Sən taxılçılıq üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda buğda və arpa becərmə haqqında dərin biliyə maliksən.
Payızlıq və yazlıq taxıllar, don zədəsi, alaq otlarına qarşı mübarizə və məhsuldarlığın artırılması haqqında ətraflı məlumat ver.
""",
    "orchard": """
Sən meyvəçilik üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda alma, üzüm, fındıq və digər meyvə bağlarının becərilməsi haqqında dərin biliyə maliksən.
Budama, çiçəklənmə, zərərvericilərə qarşı mübarizə və məhsul yığımı haqqında ətraflı məlumat ver.
""",
    "vegetable": """
Sən tərəvəzçilik üzrə ixtisaslaşmış aqronomiqa ekspertisən.
Azərbaycanda pomidor, xıyar, bibər və digər tərəvəzlərin becərilməsi haqqında dərin biliyə maliksən.
İstixana və açıq sahədə tərəvəz yetişdirilməsi, suvarma və gübrələmə haqqında ətraflı məlumat ver.
""",
    "livestock": """
Sən heyvandarlıq üzrə ixtisaslaşmış mütəxəssissən.
Azərbaycanda mal-qara, qoyun, keçi və quşçuluq haqqında dərin biliyə maliksən.
Yemləmə, sağlamlıq, peyvəndləmə və məhsuldarlıq haqqında ətraflı məlumat ver.
""",
    "advanced": """
Sən kənd təsərrüfatı üzrə yüksək ixtisaslı ekspertsən.
Cavablarını daha texniki və ətraflı ver. Torpaq analizləri, bitki fiziologiyası, iqtisadi hesablamalar və GIS məlumatları daxil et.
Lazım gəldikdə elmi terminologiya istifadə et, lakin izah da ver.
""",
}
