"""
Yonca AI - Modern Streamlit Styles
==================================

Clean, mobile-first CSS for the Yonca farm assistant app.
Designed for Azerbaijani farmers with familiar UI patterns.

Design Principles:
- Mobile-first (390-430px viewport)
- Yonca brand: Forest Green (#2E7D32) + Soft Mint (#A5D6A7)
- High contrast for outdoor visibility
- Theme-aware (light/dark mode support)
"""
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Brand colors
    "primary": "#2E7D32",
    "primary_dark": "#1B5E20",
    "primary_light": "#4CAF50",
    "secondary": "#A5D6A7",
    "secondary_light": "#C8E6C9",
    
    # Background & surface
    "background": "#F8F9FA",
    "surface": "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    
    # Text
    "text_primary": "#1A1A1A",
    "text_secondary": "#666666",
    "text_on_primary": "#FFFFFF",
    
    # Priority colors
    "critical": "#C62828",
    "critical_bg": "#FFEBEE",
    "high": "#E65100",
    "high_bg": "#FFF3E0",
    "medium": "#F9A825",
    "medium_bg": "#FFFDE7",
    "low": "#2E7D32",
    "low_bg": "#E8F5E9",
    
    # Chat
    "chat_user": "#DCF8C6",
    "chat_bot": "#FFFFFF",
    
    # Utility
    "border": "#E0E0E0",
    "shadow": "rgba(0,0,0,0.08)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CSS STYLES
# ═══════════════════════════════════════════════════════════════════════════════

def get_base_css() -> str:
    """Base CSS for the app layout."""
    return f"""
    <style>
        /* Hide Streamlit branding */
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        
        /* Mobile-first container */
        .block-container {{
            padding: 1rem !important;
            max-width: 430px !important;
            margin: 0 auto !important;
        }}
        
        .main {{
            background-color: {COLORS['background']} !important;
        }}
        
        /* Smooth transitions */
        * {{
            transition: background-color 0.2s, color 0.2s, border-color 0.2s;
        }}
    </style>
    """


def get_header_css() -> str:
    """CSS for the app header."""
    return f"""
    <style>
        .app-header {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
            color: {COLORS['text_on_primary']};
            padding: 12px 16px;
            border-radius: 0 0 16px 16px;
            margin: -1rem -1rem 1rem -1rem;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 12px {COLORS['shadow']};
        }}
        
        .header-icon {{
            font-size: 1.8rem;
            background: rgba(255,255,255,0.15);
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .header-content {{
            flex: 1;
        }}
        
        .header-content h1 {{
            margin: 0;
            font-size: 1.2rem;
            font-weight: 600;
        }}
        
        .header-content .subtitle {{
            font-size: 0.75rem;
            opacity: 0.9;
            margin-top: 2px;
        }}
        
        .header-greeting {{
            font-size: 0.8rem;
            text-align: right;
        }}
        
        .header-greeting .farmer-name {{
            font-weight: 600;
        }}
    </style>
    """


def get_card_css() -> str:
    """CSS for insight/recommendation cards."""
    return f"""
    <style>
        /* Farm Profile Card */
        .farm-profile-card {{
            background: {COLORS['surface']};
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px {COLORS['shadow']};
            border: 1px solid {COLORS['border']};
        }}
        
        .profile-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        
        .profile-icon {{
            font-size: 2rem;
            background: {COLORS['secondary_light']};
            width: 56px;
            height: 56px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .profile-info h3 {{
            margin: 0;
            font-size: 1.1rem;
            color: {COLORS['text_primary']};
        }}
        
        .profile-region {{
            font-size: 0.8rem;
            color: {COLORS['text_secondary']};
        }}
        
        .profile-stats {{
            font-size: 0.85rem;
            color: {COLORS['text_secondary']};
            padding: 10px;
            background: {COLORS['background']};
            border-radius: 10px;
        }}
        
        .profile-alert {{
            margin-top: 12px;
            padding: 10px 12px;
            background: {COLORS['critical_bg']};
            border-left: 4px solid {COLORS['critical']};
            border-radius: 8px;
            font-size: 0.85rem;
            color: {COLORS['critical']};
        }}
        
        /* Insight Cards */
        .insight-card {{
            background: {COLORS['surface']};
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: 0 2px 6px {COLORS['shadow']};
            border-left: 4px solid {COLORS['primary']};
        }}
        
        .insight-card.critical {{
            border-left-color: {COLORS['critical']};
            background: linear-gradient(90deg, {COLORS['critical_bg']} 0%, {COLORS['surface']} 30%);
        }}
        
        .insight-card.high {{
            border-left-color: {COLORS['high']};
            background: linear-gradient(90deg, {COLORS['high_bg']} 0%, {COLORS['surface']} 30%);
        }}
        
        .insight-card.medium {{
            border-left-color: {COLORS['medium']};
        }}
        
        .insight-card.low {{
            border-left-color: {COLORS['low']};
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        
        .card-title {{
            font-size: 1rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
            flex: 1;
        }}
        
        .priority-badge {{
            font-size: 0.65rem;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .priority-badge.critical {{
            background: {COLORS['critical']};
            color: white;
        }}
        
        .priority-badge.high {{
            background: {COLORS['high']};
            color: white;
        }}
        
        .priority-badge.medium {{
            background: {COLORS['medium']};
            color: {COLORS['text_primary']};
        }}
        
        .priority-badge.low {{
            background: {COLORS['secondary']};
            color: {COLORS['primary_dark']};
        }}
        
        .card-description {{
            font-size: 0.9rem;
            color: {COLORS['text_secondary']};
            margin-bottom: 12px;
            line-height: 1.5;
        }}
        
        .card-action {{
            background: {COLORS['secondary_light']};
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
        }}
        
        .action-title {{
            font-size: 0.8rem;
            font-weight: 600;
            color: {COLORS['primary_dark']};
            margin-bottom: 4px;
        }}
        
        .action-text {{
            font-size: 0.85rem;
            color: {COLORS['text_primary']};
        }}
        
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: {COLORS['text_secondary']};
            margin-top: 10px;
        }}
        
        .confidence {{
            color: {COLORS['primary']};
            font-weight: 500;
        }}
        
        .time-slot {{
            color: {COLORS['high']};
        }}
        
        /* Why Section */
        .why-section {{
            margin-top: 10px;
            border-top: 1px dashed {COLORS['border']};
            padding-top: 10px;
        }}
        
        .why-section summary {{
            font-size: 0.85rem;
            color: {COLORS['primary']};
            cursor: pointer;
            font-weight: 500;
        }}
        
        .why-section p {{
            font-size: 0.8rem;
            color: {COLORS['text_secondary']};
            margin-top: 8px;
            padding: 10px;
            background: {COLORS['background']};
            border-radius: 8px;
            line-height: 1.5;
        }}
        
        /* Recommendations Summary */
        .recs-summary {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: {COLORS['secondary_light']};
            border-radius: 10px;
            margin-bottom: 16px;
            font-size: 0.85rem;
        }}
        
        .recs-summary .critical-badge {{
            color: {COLORS['critical']};
            font-weight: 600;
        }}
        
        .recs-summary .meta {{
            font-size: 0.75rem;
            color: {COLORS['text_secondary']};
        }}
    </style>
    """


def get_timeline_css() -> str:
    """CSS for the daily timeline."""
    return f"""
    <style>
        .timeline-item {{
            display: flex;
            gap: 12px;
            padding: 12px;
            background: {COLORS['surface']};
            border-radius: 12px;
            margin-bottom: 10px;
            box-shadow: 0 1px 4px {COLORS['shadow']};
            border-left: 3px solid {COLORS['primary']};
        }}
        
        .timeline-item.critical {{
            border-left-color: {COLORS['critical']};
        }}
        
        .timeline-item.high {{
            border-left-color: {COLORS['high']};
        }}
        
        .timeline-time {{
            font-size: 0.9rem;
            font-weight: 600;
            color: {COLORS['primary']};
            min-width: 50px;
        }}
        
        .timeline-content {{
            display: flex;
            gap: 10px;
            flex: 1;
        }}
        
        .timeline-icon {{
            font-size: 1.3rem;
        }}
        
        .timeline-details {{
            flex: 1;
        }}
        
        .timeline-title {{
            font-size: 0.9rem;
            font-weight: 600;
            color: {COLORS['text_primary']};
        }}
        
        .timeline-desc {{
            font-size: 0.8rem;
            color: {COLORS['text_secondary']};
            margin-top: 2px;
        }}
        
        .timeline-duration {{
            font-size: 0.75rem;
            color: {COLORS['text_secondary']};
            margin-top: 4px;
        }}
    </style>
    """


def get_chat_css() -> str:
    """CSS for the chat interface."""
    return f"""
    <style>
        .chat-bubble {{
            max-width: 85%;
            padding: 12px 14px;
            border-radius: 16px;
            margin-bottom: 10px;
            line-height: 1.5;
        }}
        
        .chat-bubble.user {{
            background: {COLORS['chat_user']};
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}
        
        .chat-bubble.assistant {{
            background: {COLORS['chat_bot']};
            border: 1px solid {COLORS['border']};
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }}
        
        .bubble-content {{
            font-size: 0.9rem;
            color: {COLORS['text_primary']};
        }}
        
        .bubble-time {{
            font-size: 0.7rem;
            color: {COLORS['text_secondary']};
            margin-top: 6px;
            text-align: right;
        }}
    </style>
    """


def get_footer_css() -> str:
    """CSS for the app footer."""
    return f"""
    <style>
        .app-footer {{
            text-align: center;
            font-size: 0.75rem;
            color: {COLORS['text_secondary']};
            padding: 16px 0;
            line-height: 1.6;
        }}
    </style>
    """


def apply_custom_styles():
    """Apply all custom CSS styles to the Streamlit app."""
    all_css = (
        get_base_css() +
        get_header_css() +
        get_card_css() +
        get_timeline_css() +
        get_chat_css() +
        get_footer_css()
    )
    st.markdown(all_css, unsafe_allow_html=True)
