"""
Yonca AI - Fermer Köməkçisi
===========================

Modern Streamlit app for Azerbaijani farmers.
Mobile-first design with Yonca brand colors.

Features:
- 🌾 5 farm scenario profiles (wheat, livestock, orchard, mixed, poultry)
- 🤖 AI-powered recommendations via Sidecar Intelligence
- 💬 Natural language chat in Azerbaijani
- 📅 Daily task scheduling
- 🌡️ Weather & soil monitoring
"""
import sys
from pathlib import Path

# Ensure src is in path for Streamlit Cloud deployment
_src_path = Path(__file__).resolve().parent.parent.parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

import streamlit as st
from datetime import datetime

# Local imports
from yonca.umbrella.core import (
    ScenarioProfile,
    SCENARIO_LABELS,
    UIFarmProfile,
    load_farm_for_scenario,
    generate_recommendations,
    generate_chat_response,
)
from yonca.umbrella.styles import apply_custom_styles


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Yonca AI - Fermer Köməkçisi",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Apply custom CSS
apply_custom_styles()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def init_session():
    """Initialize session state with defaults."""
    defaults = {
        "current_profile": ScenarioProfile.WHEAT,
        "current_farm": None,
        "recommendations": None,
        "chat_history": [],
        "request_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Load initial farm if needed
    if st.session_state.current_farm is None:
        st.session_state.current_farm = load_farm_for_scenario(
            st.session_state.current_profile
        )

init_session()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def switch_scenario(profile: ScenarioProfile):
    """Switch to a new farm scenario."""
    st.session_state.current_profile = profile
    st.session_state.current_farm = load_farm_for_scenario(profile)
    st.session_state.recommendations = None


def refresh_recommendations():
    """Generate fresh AI recommendations."""
    with st.spinner("🤖 AI təhlil edir..."):
        farm = st.session_state.current_farm
        st.session_state.recommendations = generate_recommendations(farm)
        st.session_state.request_count += 1


def send_chat_message(message: str):
    """Send a chat message and get AI response."""
    farm = st.session_state.current_farm
    timestamp = datetime.now().strftime("%H:%M")
    
    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": message,
        "time": timestamp,
    })
    
    # Generate AI response
    response = generate_chat_response(message, farm)
    st.session_state.chat_history.append({
        "role": "assistant", 
        "content": response,
        "time": timestamp,
    })


def clear_chat():
    """Clear chat history."""
    st.session_state.chat_history = []


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def render_header():
    """Render the app header with Yonca branding."""
    profile = st.session_state.current_profile
    label = SCENARIO_LABELS[profile]
    farmer_name = label.get("farmer_name", "Fermer")
    
    st.markdown(f"""
    <div class="app-header">
        <div class="header-icon">🌿</div>
        <div class="header-content">
            <h1>Yonca AI</h1>
            <div class="subtitle">Şəxsi Fermer Köməkçiniz</div>
        </div>
        <div class="header-greeting">
            Salam, <span class="farmer-name">{farmer_name}</span>! 👋
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_scenario_selector():
    """Render farm scenario selection buttons."""
    st.markdown("### 🔄 Təsərrüfat Seçimi")
    
    cols = st.columns(5)
    for idx, profile in enumerate(ScenarioProfile):
        label = SCENARIO_LABELS[profile]
        is_active = st.session_state.current_profile == profile
        
        with cols[idx]:
            btn_type = "primary" if is_active else "secondary"
            help_text = f"{label['name']}: {label['description']}"
            
            if st.button(
                label["icon"],
                key=f"scenario_{profile.value}",
                type=btn_type,
                use_container_width=True,
                help=help_text,
            ):
                switch_scenario(profile)
                st.rerun()


def render_farm_profile_card(farm: UIFarmProfile):
    """Render the farm profile summary card."""
    label = SCENARIO_LABELS[farm.profile_type]
    
    # Build stats
    stats = []
    
    if farm.soil:
        stats.append(f"💧 Nəmlik: {farm.soil.moisture_percent}%")
        stats.append(f"🧪 pH: {farm.soil.ph_level}")
    
    if farm.weather:
        stats.append(f"🌡️ {farm.weather.temperature_current}°C")
        stats.append(f"💨 {farm.weather.humidity_percent}% rütubət")
    
    if farm.crops:
        stats.append(f"🌾 {len(farm.crops)} bitki növü")
    
    if farm.livestock:
        total = sum(l.count for l in farm.livestock)
        stats.append(f"🐄 {total} baş heyvan")
    
    stats_html = " • ".join(stats[:4])
    
    # Check for alerts
    alert_html = ""
    if farm.satellite_alert:
        alert_html = f'<div class="profile-alert">⚠️ {farm.satellite_alert}</div>'
    elif farm.weather and farm.weather.humidity_percent > 70 and farm.weather.temperature_max > 32:
        alert_html = '<div class="profile-alert">⚠️ İstilik stresi riski: Yüksək temperatur + rütubət</div>'
    
    st.markdown(f"""
    <div class="farm-profile-card">
        <div class="profile-header">
            <span class="profile-icon">{label['icon']}</span>
            <div class="profile-info">
                <h3>{farm.name}</h3>
                <span class="profile-region">📍 {farm.region} • {farm.area_hectares} ha</span>
            </div>
        </div>
        <div class="profile-stats">{stats_html}</div>
        {alert_html}
    </div>
    """, unsafe_allow_html=True)


def render_recommendations_tab():
    """Render the AI recommendations tab."""
    st.markdown("### 🤖 AI Tövsiyələri")
    st.caption("Qwen2.5-7B modeli tərəfindən hazırlanmış şəxsi tövsiyələr")
    
    # Refresh button
    if st.button("🔄 Tövsiyələri Yenilə", type="primary", use_container_width=True):
        refresh_recommendations()
        st.rerun()
    
    # Display recommendations
    recs = st.session_state.recommendations
    if recs:
        # Summary bar
        critical = sum(1 for r in recs["items"] if r["priority"] == "critical")
        
        st.markdown(f"""
        <div class="recs-summary">
            <span>🎯 {len(recs['items'])} tövsiyə</span>
            <span class="critical-badge">🚨 {critical} kritik</span>
            <span class="meta">⚡ {recs['processing_ms']}ms</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendation cards
        for rec in recs["items"]:
            render_recommendation_card(rec)
    else:
        st.info("💡 Tövsiyələri görmək üçün yuxarıdakı düyməni basın.")


def render_recommendation_card(rec: dict):
    """Render a single recommendation card."""
    priority = rec.get("priority", "medium")
    priority_labels = {
        "critical": ("KRİTİK", "critical"),
        "high": ("YÜKSƏK", "high"),
        "medium": ("ORTA", "medium"),
        "low": ("AŞAĞI", "low"),
    }
    label, css_class = priority_labels.get(priority, ("ORTA", "medium"))
    
    confidence = rec.get("confidence", 0.85)
    confidence_pct = int(confidence * 100)
    
    time_html = f"<span class='time-slot'>⏰ {rec['time']}</span>" if rec.get('time') else ""
    
    st.markdown(f"""
    <div class="insight-card {css_class}">
        <div class="card-header">
            <span class="card-title">{rec['title']}</span>
            <span class="priority-badge {css_class}">{label}</span>
        </div>
        <p class="card-description">{rec['description']}</p>
        <div class="card-action">
            <div class="action-title">✅ Tövsiyə olunan addım:</div>
            <div class="action-text">{rec['action']}</div>
        </div>
        <div class="card-footer">
            <span class="confidence">📊 Etibarlılıq: {confidence_pct}%</span>
            {time_html}
        </div>
        <details class="why-section">
            <summary>❓ Niyə bu tövsiyə?</summary>
            <p>{rec.get('why', 'Bu tövsiyə mövcud verilənlər əsasında hazırlanıb.')}</p>
        </details>
    </div>
    """, unsafe_allow_html=True)


def render_timeline_tab():
    """Render the daily schedule timeline tab."""
    st.markdown("### 📅 Gündəlik Cədvəl")
    st.caption(f"Bu gün: {datetime.now().strftime('%d.%m.%Y')}")
    
    recs = st.session_state.recommendations
    if recs and recs.get("routine"):
        for item in recs["routine"]:
            render_timeline_item(item)
    else:
        st.info("📋 Gündəlik cədvəl üçün əvvəlcə tövsiyələri yükləyin.")


def render_timeline_item(item: dict):
    """Render a single timeline item."""
    priority = item.get("priority", "medium")
    
    st.markdown(f"""
    <div class="timeline-item {priority}">
        <div class="timeline-time">{item['time']}</div>
        <div class="timeline-content">
            <span class="timeline-icon">{item['icon']}</span>
            <div class="timeline-details">
                <div class="timeline-title">{item['title']}</div>
                <div class="timeline-desc">{item['description']}</div>
                <div class="timeline-duration">⏱️ {item['duration']} dəq</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_tab():
    """Render the chat interface tab."""
    st.markdown("### 💬 Yonca AI ilə Söhbət")
    
    farm = st.session_state.current_farm
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Welcome message if empty
        if not st.session_state.chat_history:
            st.markdown(f"""
            <div class="chat-bubble assistant">
                <div class="bubble-content">
                    Salam! 👋 Mən Yonca AI köməkçisiyəm.<br><br>
                    Hazırda <strong>{farm.name}</strong> təsərrüfatı üzərində işləyirik.<br><br>
                    Sizə necə kömək edə bilərəm?
                </div>
                <div class="bubble-time">{datetime.now().strftime("%H:%M")}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render chat history
            for msg in st.session_state.chat_history:
                role = msg["role"]
                st.markdown(f"""
                <div class="chat-bubble {role}">
                    <div class="bubble-content">{msg['content']}</div>
                    <div class="bubble-time">{msg['time']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Quick reply suggestions
    st.markdown("**Sürətli suallar:**")
    
    quick_replies = [
        ("💧 Suvarma", "Nə vaxt suvarmalıyam?"),
        ("🌱 Gübrə", "Gübrə lazımdırmı?"),
        ("🐛 Xəstəlik", "Xəstəlik riski varmı?"),
        ("📋 Plan", "Bu gün nə edim?"),
        ("🌤️ Hava", "Hava necə olacaq?"),
    ]
    
    cols = st.columns(3)
    for idx, (label, question) in enumerate(quick_replies):
        with cols[idx % 3]:
            if st.button(label, key=f"quick_{idx}", use_container_width=True):
                send_chat_message(question)
                st.rerun()
    
    # Free text input
    user_input = st.chat_input("Sualınızı yazın...")
    if user_input:
        send_chat_message(user_input)
        st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Söhbəti Təmizlə", use_container_width=True):
            clear_chat()
            st.rerun()


def render_footer():
    """Render the app footer."""
    st.markdown("---")
    st.markdown("""
    <div class="app-footer">
        🌿 Yonca AI v0.3.0 | Digital Umbrella Prototype<br>
        100% Sintetik Data | Qwen2.5-7B Inference<br>
        © 2026 Digital Umbrella
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with settings."""
    with st.sidebar:
        st.markdown("### ⚙️ Tənzimləmələr")
        
        st.selectbox(
            "🌐 Dil",
            ["🇦🇿 Azərbaycan", "🇬🇧 English", "🇷🇺 Русский"],
            index=0,
        )
        
        st.markdown("---")
        
        st.markdown("**📊 Sistem Məlumatı:**")
        st.code(f"""
Profil: {st.session_state.current_profile.value}
Sorğular: {st.session_state.request_count}
Mesajlar: {len(st.session_state.chat_history)}
        """)
        
        st.markdown("---")
        st.markdown("""
        **🔗 Faydalı Keçidlər:**
        - [API Docs](/docs)
        - [GitHub](https://github.com/Px8Studio/yonja)
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""
    # Header
    render_header()
    
    # Scenario selector
    render_scenario_selector()
    
    st.markdown("---")
    
    # Farm profile card
    farm = st.session_state.current_farm
    if farm:
        render_farm_profile_card(farm)
    
    # Main tabs
    tab_recs, tab_timeline, tab_chat = st.tabs([
        "📋 Tövsiyələr",
        "📅 Gündəlik Plan", 
        "💬 Söhbət"
    ])
    
    with tab_recs:
        render_recommendations_tab()
    
    with tab_timeline:
        render_timeline_tab()
    
    with tab_chat:
        render_chat_tab()
    
    # Footer
    render_footer()
    
    # Sidebar
    render_sidebar()


# Run the app
if __name__ == "__main__":
    main()
else:
    # Also run when imported by Streamlit
    main()
