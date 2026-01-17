"""
Yonca AI - Digital Umbrella Streamlit App
==========================================

Mobile-first "Personalized Farm Assistant" prototype.
Primary language: Azerbaijani (az)

Usage:
    streamlit run src/yonca/umbrella/app.py

Features:
    1. Scenario Switcher - Toggle between 5 farm profiles
    2. Profile Overview - Synthetic data display
    3. AI Advisory - Core value proposition with insight cards
    4. Simple Chat - Intent-based Azerbaijani chatbot
"""

import streamlit as st
from datetime import datetime

# Import our modules
from yonca.umbrella.scenario_manager import (
    ScenarioManager,
    ScenarioProfile,
    SCENARIO_LABELS,
)
from yonca.umbrella.mock_backend import (
    MockBackend,
    FarmProfileRequest,
)
from yonca.umbrella.agronomy_rules import AgronomyLogicGuard
from yonca.umbrella.styles import (
    get_all_styles,
    render_header,
    render_insight_card,
    render_chat_bubble,
    render_timeline_item,
    render_profile_card,
    COLORS,
)

# Import unified intent matcher from sidecar (consolidation)
from yonca.sidecar.intent_matcher import get_intent_matcher, IntentMatch


# ============= PAGE CONFIG =============

st.set_page_config(
    page_title="Yonca AI - Fermer Köməkçisi",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============= SESSION STATE INITIALIZATION =============

def init_session_state():
    """Initialize session state variables."""
    if "scenario_manager" not in st.session_state:
        st.session_state.scenario_manager = ScenarioManager()
    
    if "backend" not in st.session_state:
        logic_guard = AgronomyLogicGuard()
        st.session_state.backend = MockBackend(logic_guard=logic_guard)
    
    if "current_profile" not in st.session_state:
        st.session_state.current_profile = ScenarioProfile.WHEAT
    
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "tövsiyələr"


init_session_state()


# ============= INTENT-BASED CHAT RESPONSE (Unified) =============

# Get the singleton intent matcher
_intent_matcher = get_intent_matcher()


def generate_chat_response(user_message: str, farm) -> str:
    """
    Generate an intent-based response in Azerbaijani.
    
    Uses the unified IntentMatcher from sidecar module for
    dialect-aware, pattern-based intent detection.
    
    This simulates Qwen2.5-7B inference for demo purposes.
    """
    # Use unified intent matcher
    intent_result: IntentMatch = _intent_matcher.match(user_message)
    intent = intent_result.intent
    confidence = intent_result.confidence
    
    # Log for debugging (visible in console)
    # print(f"[Intent] {intent} ({confidence:.0%}) - patterns: {intent_result.matched_patterns}")
    
    # Route to appropriate handler based on detected intent
    if intent == "irrigation":
        if farm.soil:
            moisture = farm.soil.moisture_percent
            if moisture < 25:
                return (
                    f"🚨 **Təcili suvarma tövsiyəsi!**\n\n"
                    f"Torpaq nəmliyi {moisture}% - kritik səviyyədədir.\n\n"
                    "**Tövsiyə:** Bu gün saat 06:00-08:00 arasında suvarmanı başlayın. "
                    "Hər hektara 40-50mm su verin.\n\n"
                    "❓ *Niyə?* Çiçəkləmə dövründə su stresi məhsuldarlığı 30%-ə qədər azalda bilər.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            elif moisture < 40:
                return (
                    f"💧 **Suvarma planlaşdırın**\n\n"
                    f"Torpaq nəmliyi {moisture}% - orta səviyyədədir.\n\n"
                    "**Tövsiyə:** Sabah səhər suvarma tövsiyə olunur. "
                    "Damcı suvarma sistemindən istifadə edin.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            else:
                return (
                    f"✅ **Suvarma lazım deyil**\n\n"
                    f"Torpaq nəmliyi {moisture}% - optimal səviyyədədir.\n\n"
                    "Növbəti yoxlama 2 gün sonra.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
        return "Torpaq məlumatları mövcud deyil. Əvvəlcə nəmlik ölçmə aparın."
    
    # Fertilization intent
    elif intent == "fertilization":
        if farm.soil:
            nitrogen = farm.soil.nitrogen_kg_ha
            if nitrogen < 25:
                return (
                    f"🌱 **Azot gübrəsi tövsiyəsi**\n\n"
                    f"Azot səviyyəsi {nitrogen} kq/ha - aşağıdır.\n\n"
                    "**Tövsiyə:** Ammonium nitrat (NH₄NO₃) gübrəsini 80-100 kq/ha dozasında tətbiq edin.\n\n"
                    "⏰ *Ən yaxşı vaxt:* Səhər suvarması ilə birlikdə\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            else:
                return (
                    f"✅ **Gübrə hazırda lazım deyil**\n\n"
                    f"Azot səviyyəsi {nitrogen} kq/ha - normal həddədədir.\n\n"
                    "2 həftə sonra yenidən yoxlayın.\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
        return "Torpaq analizi məlumatı mövcud deyil."
    
    # Disease/pest intent (matches both "disease" and "pest_control" from intent matcher)
    elif intent in ("disease", "pest_control"):
        if farm.weather and farm.weather.humidity_percent > 70:
            return (
                f"⚠️ **Xəstəlik riski yüksəkdir!**\n\n"
                f"Hazırkı rütubət {farm.weather.humidity_percent}% - göbələk xəstəlikləri üçün əlverişlidir.\n\n"
                "**Diqqət edin:**\n"
                "• Yarpaq ləkələri\n"
                "• Unlu şeh əlamətləri\n"
                "• Gövdə çürüməsi\n\n"
                "**Tövsiyə:** Fungisid tətbiqi planlaşdırın.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return (
            "✅ **Xəstəlik riski aşağıdır**\n\n"
            "Hazırkı şərait normal həddədədir. Həftəlik vizual müayinə davam edin.\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    
    # Planting intent (for schedule questions)
    elif intent == "planting":
        return (
            f"📋 **{datetime.now().strftime('%d.%m.%Y')} üçün plan:**\n\n"
            "1. **06:00** - Sahə müayinəsi\n"
            "2. **07:00** - Suvarma (əgər lazımdırsa)\n"
            "3. **09:00** - Gübrə tətbiqi\n"
            "4. **11:00-16:00** - İstirahət (günorta istisi)\n"
            "5. **17:00** - Avadanlıq baxımı\n\n"
            "📌 *\"Gündəlik Plan\" tabına baxın detallı cədvəl üçün.*\n\n"
            f"📊 *Etibarlılıq: {confidence:.0%}*"
        )
    
    # Weather intent
    elif intent == "weather":
        if farm.weather:
            w = farm.weather
            rain_status = "🌧️ Yağış gözlənilir" if w.condition == "rainy" else "☀️ Quru hava"
            return (
                f"🌤️ **Hava proqnozu**\n\n"
                f"Hazırda: {w.temperature_current}°C, {w.condition}\n"
                f"Min/Maks: {w.temperature_min}°C / {w.temperature_max}°C\n"
                f"Rütubət: {w.humidity_percent}%\n"
                f"Külək: {w.wind_speed_kmh} km/saat\n\n"
                f"**Proqnoz:** {rain_status}\n\n"
                f"*Yağış planlarınızı suvarma cədvəlinə uyğunlaşdırın.*\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Hava məlumatı mövcud deyil."
    
    # Livestock intent
    elif intent == "livestock":
        if farm.livestock:
            total = sum(l.count for l in farm.livestock)
            animals = ", ".join([f"{l.count} {l.animal_type}" for l in farm.livestock])
            
            if farm.weather and farm.weather.humidity_percent > 70 and farm.weather.temperature_max > 30:
                return (
                    f"🐄 **Heyvandarlıq vəziyyəti**\n\n"
                    f"Cəmi: {total} baş ({animals})\n\n"
                    "⚠️ **DİQQƏT: İstilik stresi riski!**\n\n"
                    "• Ventilyasiya sistemini yoxlayın\n"
                    "• Əlavə su mənbələri təmin edin\n"
                    "• Günorta yemlənməni təxirə salın\n"
                    "• Respirator simptomlara diqqət edin\n\n"
                    f"📊 *Etibarlılıq: {confidence:.0%}*"
                )
            return (
                f"🐄 **Heyvandarlıq vəziyyəti**\n\n"
                f"Cəmi: {total} baş ({animals})\n\n"
                "✅ Şərait normaldır. Gündəlik sağlamlıq yoxlamasını davam edin.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Bu təsərrüfatda heyvandarlıq məlumatı yoxdur."
    
    # Soil intent
    elif intent == "soil":
        if farm.soil:
            return (
                f"🌱 **Torpaq Analizi**\n\n"
                f"• Nəmlik: {farm.soil.moisture_percent}%\n"
                f"• pH: {farm.soil.ph_level}\n"
                f"• Azot (N): {farm.soil.nitrogen_kg_ha} kq/ha\n"
                f"• Fosfor (P): {farm.soil.phosphorus_kg_ha} kq/ha\n"
                f"• Kalium (K): {farm.soil.potassium_kg_ha} kq/ha\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Torpaq analizi məlumatı mövcud deyil."
    
    # Harvest intent
    elif intent == "harvest":
        if farm.crops:
            crop = farm.crops[0]
            return (
                f"🌾 **Məhsul Yığımı**\n\n"
                f"Bitki: {crop.crop_type}\n"
                f"Mərhələ: {crop.growth_stage}\n\n"
                "**Tövsiyə:** Məhsul yığımından əvvəl torpaq nəmliyini yoxlayın.\n\n"
                f"📊 *Etibarlılıq: {confidence:.0%}*"
            )
        return "Bitki məlumatı mövcud deyil."
    
    # Check for greeting patterns in the original message
    msg_lower = user_message.lower()
    if any(word in msg_lower for word in ["salam", "xoş", "necəsən", "hello", "hi"]):
        return (
            f"Salam! 👋\n\n"
            f"Mən Yonca AI - sizin şəxsi fermer köməkçinizəm.\n\n"
            f"Hazırda **{farm.name}** ({farm.region}) üzərində işləyirik.\n\n"
            "Sizə necə kömək edə bilərəm?"
        )
    
    # Help keywords
    if any(word in msg_lower for word in ["kömək", "help", "nə edə bilərsən", "imkan"]):
        return (
            "🌿 **Yonca AI ilə nə edə bilərsiniz:**\n\n"
            "🌊 **Suvarma** - \"Nə vaxt suvarmalıyam?\"\n"
            "🌱 **Gübrələmə** - \"Gübrə lazımdırmı?\"\n"
            "🐛 **Xəstəliklər** - \"Xəstəlik riski varmı?\"\n"
            "📋 **Cədvəl** - \"Bu gün nə edim?\"\n"
            "🌤️ **Hava** - \"Hava necə olacaq?\"\n"
            "🐄 **Heyvandarlıq** - \"Peyvənd lazımdırmı?\"\n\n"
            "*İstənilən sualınızı Azərbaycan dilində yaza bilərsiniz!*"
        )
    
    # Plan/schedule keywords (fallback)
    if any(word in msg_lower for word in ["bu gün", "plan", "cədvəl", "nə edim", "işlər"]):
        return (
            f"📋 **{datetime.now().strftime('%d.%m.%Y')} üçün plan:**\n\n"
            "1. **06:00** - Sahə müayinəsi\n"
            "2. **07:00** - Suvarma (əgər lazımdırsa)\n"
            "3. **09:00** - Gübrə tətbiqi\n"
            "4. **11:00-16:00** - İstirahət (günorta istisi)\n"
            "5. **17:00** - Avadanlıq baxımı\n\n"
            "📌 *\"Gündəlik Plan\" tabına baxın detallı cədvəl üçün.*"
        )
    
    # Default response with detected intent info
    return (
        "🤔 Sualınızı tam başa düşmədim.\n\n"
        "Aşağıdakı mövzularda kömək edə bilərəm:\n"
        "• Suvarma tövsiyələri\n"
        "• Gübrələmə planı\n"
        "• Xəstəlik/zərərverici monitorinqi\n"
        "• Gündəlik iş cədvəli\n"
        "• Hava proqnozu\n\n"
        "*Yenidən soruşun və ya \"Kömək\" yazın.*"
    )


# ============= INJECT CSS =============

st.markdown(get_all_styles(), unsafe_allow_html=True)


# ============= HEADER =============

st.markdown(
    render_header(
        title="Yonca AI",
        subtitle="Şəxsi Fermer Köməkçiniz",
        icon="🌿"
    ),
    unsafe_allow_html=True
)


# ============= SCENARIO SWITCHER =============

st.markdown("### 🔄 Təsərrüfat Seçimi")

# Create columns for scenario buttons
cols = st.columns(5)

for idx, profile in enumerate(ScenarioProfile):
    label = SCENARIO_LABELS[profile]
    with cols[idx]:
        is_active = st.session_state.current_profile == profile
        
        if st.button(
            f"{label['icon']}\n{label['name'][:8]}...",
            key=f"scenario_{profile.value}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.current_profile = profile
            st.session_state.scenario_manager.switch_profile(profile)
            st.session_state.recommendations = None  # Reset recommendations
            st.rerun()

st.markdown("---")


# ============= GET CURRENT FARM DATA =============

current_farm = st.session_state.scenario_manager.current_farm
label = SCENARIO_LABELS[st.session_state.current_profile]


# ============= PROFILE OVERVIEW CARD =============

def build_profile_stats():
    """Build stats list based on farm type."""
    stats = []
    
    if current_farm.soil:
        stats.append(("Torpaq nəmliyi", f"{current_farm.soil.moisture_percent}%"))
        stats.append(("Torpaq pH", f"{current_farm.soil.ph_level}"))
    
    if current_farm.weather:
        stats.append(("Temperatur", f"{current_farm.weather.temperature_current}°C"))
        stats.append(("Rütubət", f"{current_farm.weather.humidity_percent}%"))
    
    if current_farm.crops:
        stats.append(("Bitkilər", f"{len(current_farm.crops)} növ"))
    
    if current_farm.livestock:
        total_animals = sum(l.count for l in current_farm.livestock)
        stats.append(("Heyvanlar", f"{total_animals} baş"))
    
    return stats[:4]  # Max 4 stats for layout


# Build alert message if applicable
alert_msg = ""
if current_farm.satellite_alert:
    alert_msg = current_farm.satellite_alert
elif (current_farm.weather and 
      current_farm.weather.humidity_percent > 70 and 
      current_farm.weather.temperature_max > 32):
    alert_msg = "İstilik stresi riski: Yüksək temperatur + rütubət"

st.markdown(
    render_profile_card(
        name=current_farm.name,
        icon=label["icon"],
        farm_type=label["name"],
        region=current_farm.region,
        area=current_farm.area_hectares,
        stats=build_profile_stats(),
        alert=alert_msg
    ),
    unsafe_allow_html=True
)


# ============= TABS: Recommendations | Timeline | Chat =============

tab_recs, tab_timeline, tab_chat = st.tabs([
    "📋 Tövsiyələr",
    "📅 Gündəlik Plan",
    "💬 Söhbət"
])


# ============= TAB 1: AI RECOMMENDATIONS =============

with tab_recs:
    st.markdown("### 🤖 AI Tövsiyələri")
    st.markdown(
        f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;'>"
        "Qwen2.5-7B modeli tərəfindən hazırlanmış şəxsi tövsiyələr"
        "</p>",
        unsafe_allow_html=True
    )
    
    # Generate recommendations button
    if st.button("🔄 Tövsiyələri Yenilə", type="primary", use_container_width=True):
        with st.spinner("AI təhlil edir..."):
            # Build request from current farm
            request = FarmProfileRequest(
                farm_id=current_farm.id,
                farm_type=current_farm.profile_type.value,
                region=current_farm.region,
                area_hectares=current_farm.area_hectares,
                soil_moisture_percent=current_farm.soil.moisture_percent if current_farm.soil else None,
                soil_nitrogen=current_farm.soil.nitrogen_kg_ha if current_farm.soil else None,
                temperature_current=current_farm.weather.temperature_current if current_farm.weather else None,
                temperature_max=current_farm.weather.temperature_max if current_farm.weather else None,
                humidity_percent=current_farm.weather.humidity_percent if current_farm.weather else None,
                barn_humidity=current_farm.weather.humidity_percent if current_farm.livestock else None,
                is_rain_expected=current_farm.weather.condition == "rainy" if current_farm.weather else False,
                crops=[c.crop_type for c in current_farm.crops],
                crop_stages=[c.growth_stage for c in current_farm.crops],
                livestock_types=[l.animal_type for l in current_farm.livestock],
                livestock_counts=[l.count for l in current_farm.livestock],
                include_why_section=True,
            )
            
            # Get recommendations from mock backend
            st.session_state.recommendations = st.session_state.backend.recommend(request)
    
    # Display recommendations
    if st.session_state.recommendations:
        payload = st.session_state.recommendations
        
        # Summary
        st.markdown(
            f"""
            <div style="background:{COLORS['secondary_light']};padding:12px;border-radius:10px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.85rem;color:{COLORS['text_secondary']};">
                        🎯 {payload.total_count} tövsiyə tapıldı
                    </span>
                    <span style="font-size:0.75rem;color:{COLORS['critical']};">
                        🚨 {payload.critical_count} kritik
                    </span>
                </div>
                <div style="font-size:0.7rem;color:{COLORS['text_secondary']};margin-top:4px;">
                    ⚡ {payload.processing_time_ms}ms | 🤖 {payload.inference_engine}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Render each recommendation card
        for rec in payload.recommendations:
            st.markdown(
                render_insight_card(
                    title=rec.title,
                    description=rec.description,
                    action=rec.action,
                    priority=rec.priority.value,
                    why_title=rec.why_title,
                    why_content=rec.why_explanation,
                    confidence=rec.confidence,
                    time_slot=rec.suggested_time or ""
                ),
                unsafe_allow_html=True
            )
    else:
        st.info("Tövsiyələri görmək üçün yuxarıdakı düyməni basın.")


# ============= TAB 2: DAILY TIMELINE =============

with tab_timeline:
    st.markdown("### 📅 Gündəlik Cədvəl")
    st.markdown(
        f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;'>"
        f"Bu gün: {datetime.now().strftime('%d.%m.%Y')}"
        "</p>",
        unsafe_allow_html=True
    )
    
    # Generate or get timeline
    if st.session_state.recommendations:
        routine = st.session_state.recommendations.daily_routine
        
        # Render timeline
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        
        for item in routine:
            st.markdown(
                render_timeline_item(
                    time=item.time_slot,
                    title=item.title,
                    description=item.description,
                    icon=item.icon,
                    duration=item.duration_minutes,
                    priority=item.priority.value
                ),
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Gündəlik cədvəl üçün əvvəlcə tövsiyələri yükləyin.")


# ============= TAB 3: CHAT =============

with tab_chat:
    st.markdown("### 💬 Yonca AI ilə Söhbət")
    
    # Quick reply suggestions
    quick_replies = [
        "Nə vaxt suvarmalıyam?",
        "Gübrə lazımdırmı?",
        "Xəstəlik riski varmı?",
        "Bu gün nə edim?",
        "Hava necə olacaq?",
    ]
    
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        if not st.session_state.chat_history:
            # Welcome message
            st.markdown(
                render_chat_bubble(
                    "Salam! 👋 Mən Yonca AI köməkçisiyəm. "
                    f"Hazırda **{current_farm.name}** təsərrüfatı üzərində işləyirik. "
                    "Sizə necə kömək edə bilərəm?",
                    is_user=False,
                    timestamp=datetime.now().strftime("%H:%M")
                ),
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.chat_history:
                st.markdown(
                    render_chat_bubble(
                        msg["content"],
                        is_user=msg["is_user"],
                        timestamp=msg["timestamp"]
                    ),
                    unsafe_allow_html=True
                )
    
    # Quick reply buttons
    st.markdown("**Sürətli suallar:**")
    cols = st.columns(2)
    for idx, reply in enumerate(quick_replies):
        with cols[idx % 2]:
            if st.button(reply, key=f"quick_{idx}", use_container_width=True):
                # Add user message
                st.session_state.chat_history.append({
                    "content": reply,
                    "is_user": True,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Generate bot response
                response = generate_chat_response(reply, current_farm)
                st.session_state.chat_history.append({
                    "content": response,
                    "is_user": False,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                st.rerun()
    
    # Free text input
    user_input = st.chat_input("Sualınızı yazın...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append({
            "content": user_input,
            "is_user": True,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Generate bot response
        response = generate_chat_response(user_input, current_farm)
        st.session_state.chat_history.append({
            "content": response,
            "is_user": False,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        st.rerun()


# ============= FOOTER =============

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center;color:{COLORS['text_secondary']};font-size:0.75rem;">
        🌿 Yonca AI v0.2.0 | Digital Umbrella Prototype<br>
        100% Sintetik Data | Qwen2.5-7B Simulated Inference<br>
        © 2026 Digital Umbrella
    </div>
    """,
    unsafe_allow_html=True
)


# ============= SIDEBAR (Hidden but available) =============

with st.sidebar:
    st.markdown("### ⚙️ Tənzimləmələr")
    
    st.markdown("**Dil / Language:**")
    language = st.selectbox(
        "Seçin",
        ["🇦🇿 Azərbaycan", "🇬🇧 English", "🇷🇺 Русский"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("**Mövzu / Theme:**")
    theme = st.radio(
        "Seçin",
        ["🌿 Yaşıl (Default)", "🌙 Qaranlıq"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("**Sistem Məlumatı:**")
    st.code(f"""
Profil: {st.session_state.current_profile.value}
API Sorğuları: {st.session_state.backend._request_counter}
Chat Mesajları: {len(st.session_state.chat_history)}
    """)
    
    if st.button("🗑️ Söhbəti Təmizlə"):
        st.session_state.chat_history = []
        st.rerun()
