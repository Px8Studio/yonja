"""
Yonca AI - Digital Umbrella CSS Styles
======================================

Custom CSS for mobile-first WhatsApp/Telegram-like UI.
Designed for Azerbaijani farmers familiar with messaging apps.

Design principles:
1. Mobile-first: 390px-430px viewport simulation
2. Yonca brand colors: Forest Green (#2E7D32) + Soft Mint (#A5D6A7)
3. High contrast for outdoor visibility
4. Familiar chat bubble patterns
5. Theme-aware: Syncs with Streamlit's native light/dark themes
"""

# ============= YONCA BRAND COLORS (Light Theme - Default) =============

COLORS_LIGHT = {
    "primary": "#2E7D32",           # Forest Green
    "primary_dark": "#1B5E20",      # Darker green for headers
    "primary_light": "#4CAF50",     # Lighter green for accents
    "secondary": "#A5D6A7",         # Soft Mint
    "secondary_light": "#C8E6C9",   # Very light mint
    "background": "#F8F9FA",        # Light gray background
    "background_outer": "#E8E8E8",  # Outer container background
    "card_bg": "#FFFFFF",           # White cards
    "text_primary": "#1A1A1A",      # Darker for better contrast
    "text_secondary": "#555555",    # Darker gray for better contrast
    "text_white": "#FFFFFF",        # White text
    "critical": "#C62828",          # Darker red for better contrast
    "critical_gradient": "#FFEBEE", # Light red for critical card bg
    "high": "#E65100",              # Darker orange for better contrast
    "high_gradient": "#FFF3E0",     # Light orange for high card bg
    "medium": "#F9A825",            # Darker yellow-amber
    "medium_text": "#1A1A1A",       # Text color for medium badges
    "low": "#2E7D32",               # Use primary green for consistency
    "chat_user": "#DCF8C6",         # WhatsApp green for user messages
    "chat_bot": "#FFFFFF",          # White for bot messages
    "border": "#BDBDBD",            # Slightly darker border for visibility
    "shadow": "rgba(0,0,0,0.08)",   # Shadow color
    "shadow_strong": "rgba(0,0,0,0.1)",  # Stronger shadow
}

# ============= YONCA BRAND COLORS (Dark Theme) =============

COLORS_DARK = {
    "primary": "#4CAF50",           # Brighter green for dark mode
    "primary_dark": "#2E7D32",      # Forest green (now serves as medium)
    "primary_light": "#81C784",     # Light green for accents
    "secondary": "#1B5E20",         # Dark mint
    "secondary_light": "#2E7D32",   # Medium green for secondary elements
    "background": "#1E1E1E",        # Dark background
    "background_outer": "#121212",  # Outer container background
    "card_bg": "#2D2D2D",           # Dark cards
    "text_primary": "#E8E8E8",      # Light text for dark bg
    "text_secondary": "#B0B0B0",    # Lighter gray for secondary text
    "text_white": "#FFFFFF",        # White text (unchanged)
    "critical": "#EF5350",          # Brighter red for dark mode
    "critical_gradient": "#4A1A1A", # Dark red for critical card bg
    "high": "#FF9800",              # Brighter orange for dark mode
    "high_gradient": "#3D2E1A",     # Dark orange for high card bg
    "medium": "#FFC107",            # Brighter amber for dark mode
    "medium_text": "#1A1A1A",       # Dark text on amber badge
    "low": "#4CAF50",               # Brighter green for dark mode
    "chat_user": "#1B4D1B",         # Dark green for user messages
    "chat_bot": "#3D3D3D",          # Dark gray for bot messages
    "border": "#4A4A4A",            # Darker border for dark mode
    "shadow": "rgba(0,0,0,0.3)",    # Stronger shadow for dark mode
    "shadow_strong": "rgba(0,0,0,0.4)",  # Even stronger shadow
}

# Default to light theme colors (backward compatible)
COLORS = COLORS_LIGHT


def get_theme_css_variables() -> str:
    """
    Generate CSS custom properties that sync with Streamlit's theme.
    Uses CSS media query and Streamlit's data-theme attribute for detection.
    """
    return f"""
    <style>
        /* ============= CSS CUSTOM PROPERTIES FOR THEMING ============= */
        
        /* Light theme (default) */
        :root, [data-theme="light"], [data-testid="stAppViewContainer"]:not([data-theme="dark"]) {{
            --yonca-primary: {COLORS_LIGHT['primary']};
            --yonca-primary-dark: {COLORS_LIGHT['primary_dark']};
            --yonca-primary-light: {COLORS_LIGHT['primary_light']};
            --yonca-secondary: {COLORS_LIGHT['secondary']};
            --yonca-secondary-light: {COLORS_LIGHT['secondary_light']};
            --yonca-background: {COLORS_LIGHT['background']};
            --yonca-background-outer: {COLORS_LIGHT['background_outer']};
            --yonca-card-bg: {COLORS_LIGHT['card_bg']};
            --yonca-text-primary: {COLORS_LIGHT['text_primary']};
            --yonca-text-secondary: {COLORS_LIGHT['text_secondary']};
            --yonca-text-white: {COLORS_LIGHT['text_white']};
            --yonca-critical: {COLORS_LIGHT['critical']};
            --yonca-critical-gradient: {COLORS_LIGHT['critical_gradient']};
            --yonca-high: {COLORS_LIGHT['high']};
            --yonca-high-gradient: {COLORS_LIGHT['high_gradient']};
            --yonca-medium: {COLORS_LIGHT['medium']};
            --yonca-medium-text: {COLORS_LIGHT['medium_text']};
            --yonca-low: {COLORS_LIGHT['low']};
            --yonca-chat-user: {COLORS_LIGHT['chat_user']};
            --yonca-chat-bot: {COLORS_LIGHT['chat_bot']};
            --yonca-border: {COLORS_LIGHT['border']};
            --yonca-shadow: {COLORS_LIGHT['shadow']};
            --yonca-shadow-strong: {COLORS_LIGHT['shadow_strong']};
        }}
        
        /* Dark theme - triggered by Streamlit's dark theme */
        [data-theme="dark"],
        .stApp[data-theme="dark"],
        [data-testid="stAppViewContainer"][data-theme="dark"] {{
            --yonca-primary: {COLORS_DARK['primary']};
            --yonca-primary-dark: {COLORS_DARK['primary_dark']};
            --yonca-primary-light: {COLORS_DARK['primary_light']};
            --yonca-secondary: {COLORS_DARK['secondary']};
            --yonca-secondary-light: {COLORS_DARK['secondary_light']};
            --yonca-background: {COLORS_DARK['background']};
            --yonca-background-outer: {COLORS_DARK['background_outer']};
            --yonca-card-bg: {COLORS_DARK['card_bg']};
            --yonca-text-primary: {COLORS_DARK['text_primary']};
            --yonca-text-secondary: {COLORS_DARK['text_secondary']};
            --yonca-text-white: {COLORS_DARK['text_white']};
            --yonca-critical: {COLORS_DARK['critical']};
            --yonca-critical-gradient: {COLORS_DARK['critical_gradient']};
            --yonca-high: {COLORS_DARK['high']};
            --yonca-high-gradient: {COLORS_DARK['high_gradient']};
            --yonca-medium: {COLORS_DARK['medium']};
            --yonca-medium-text: {COLORS_DARK['medium_text']};
            --yonca-low: {COLORS_DARK['low']};
            --yonca-chat-user: {COLORS_DARK['chat_user']};
            --yonca-chat-bot: {COLORS_DARK['chat_bot']};
            --yonca-border: {COLORS_DARK['border']};
            --yonca-shadow: {COLORS_DARK['shadow']};
            --yonca-shadow-strong: {COLORS_DARK['shadow_strong']};
        }}
        
        /* Also detect via prefers-color-scheme for system theme */
        @media (prefers-color-scheme: dark) {{
            :root:not([data-theme="light"]) {{
                --yonca-primary: {COLORS_DARK['primary']};
                --yonca-primary-dark: {COLORS_DARK['primary_dark']};
                --yonca-primary-light: {COLORS_DARK['primary_light']};
                --yonca-secondary: {COLORS_DARK['secondary']};
                --yonca-secondary-light: {COLORS_DARK['secondary_light']};
                --yonca-background: {COLORS_DARK['background']};
                --yonca-background-outer: {COLORS_DARK['background_outer']};
                --yonca-card-bg: {COLORS_DARK['card_bg']};
                --yonca-text-primary: {COLORS_DARK['text_primary']};
                --yonca-text-secondary: {COLORS_DARK['text_secondary']};
                --yonca-text-white: {COLORS_DARK['text_white']};
                --yonca-critical: {COLORS_DARK['critical']};
                --yonca-critical-gradient: {COLORS_DARK['critical_gradient']};
                --yonca-high: {COLORS_DARK['high']};
                --yonca-high-gradient: {COLORS_DARK['high_gradient']};
                --yonca-medium: {COLORS_DARK['medium']};
                --yonca-medium-text: {COLORS_DARK['medium_text']};
                --yonca-low: {COLORS_DARK['low']};
                --yonca-chat-user: {COLORS_DARK['chat_user']};
                --yonca-chat-bot: {COLORS_DARK['chat_bot']};
                --yonca-border: {COLORS_DARK['border']};
                --yonca-shadow: {COLORS_DARK['shadow']};
                --yonca-shadow-strong: {COLORS_DARK['shadow_strong']};
            }}
        }}
    </style>
    """


def get_mobile_container_css() -> str:
    """
    CSS to create a mobile phone simulation container.
    Centers content in a 390-430px viewport.
    Uses CSS variables for theme support.
    """
    return """
    <style>
        /* Keep Streamlit header/menu visible for deploy button */
        /* Only hide the 'Made with Streamlit' footer */
        footer {visibility: hidden;}
        
        /* Remove default padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 430px !important;
            margin: 0 auto !important;
        }
        
        /* Mobile viewport simulation - uses CSS variables */
        .main {
            background-color: var(--yonca-background) !important;
        }
        
        /* Stacked content wrapper */
        .stApp {
            background-color: var(--yonca-background-outer);
        }
        
        /* Custom container for mobile look */
        .mobile-container {
            max-width: 430px;
            min-width: 390px;
            margin: 0 auto;
            background: var(--yonca-background);
            min-height: 100vh;
            box-shadow: 0 0 20px var(--yonca-shadow-strong);
        }
    </style>
    """


def get_header_css() -> str:
    """CSS for app header with Yonca branding."""
    return """
    <style>
        .app-header {
            background: linear-gradient(135deg, var(--yonca-primary) 0%, var(--yonca-primary-dark) 100%);
            color: var(--yonca-text-white);
            padding: 16px;
            border-radius: 0 0 20px 20px;
            margin: -1rem -1rem 1rem -1rem;
            text-align: center;
        }
        
        .app-header h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .app-header .subtitle {
            font-size: 0.85rem;
            opacity: 0.9;
            margin-top: 4px;
        }
        
        .header-icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }
    </style>
    """


def get_card_css() -> str:
    """CSS for insight cards with rounded corners."""
    return """
    <style>
        /* Base card styling */
        .insight-card {
            background: var(--yonca-card-bg);
            border-radius: 15px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px var(--yonca-shadow);
            border-left: 4px solid var(--yonca-primary);
        }
        
        .insight-card.critical {
            border-left-color: var(--yonca-critical);
            background: linear-gradient(90deg, var(--yonca-critical-gradient) 0%, var(--yonca-card-bg) 20%);
        }
        
        .insight-card.high {
            border-left-color: var(--yonca-high);
            background: linear-gradient(90deg, var(--yonca-high-gradient) 0%, var(--yonca-card-bg) 20%);
        }
        
        .insight-card.medium {
            border-left-color: var(--yonca-medium);
        }
        
        .insight-card.low {
            border-left-color: var(--yonca-low);
        }
        
        /* Card title */
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--yonca-text-primary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Priority badge */
        .priority-badge {
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .priority-badge.critical {
            background: var(--yonca-critical);
            color: white;
        }
        
        .priority-badge.high {
            background: var(--yonca-high);
            color: white;
        }
        
        .priority-badge.medium {
            background: var(--yonca-medium);
            color: var(--yonca-medium-text);
            font-weight: 600;
        }
        
        .priority-badge.low {
            background: var(--yonca-secondary);
            color: var(--yonca-primary-dark);
            font-weight: 600;
        }
        
        /* Card description */
        .card-description {
            font-size: 0.9rem;
            color: var(--yonca-text-secondary);
            margin-bottom: 12px;
            line-height: 1.5;
        }
        
        /* Action section */
        .card-action {
            background: var(--yonca-secondary-light);
            padding: 12px;
            border-radius: 10px;
            font-size: 0.85rem;
            color: var(--yonca-text-primary);
        }
        
        .card-action-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: var(--yonca-primary-dark);
        }
        
        /* Why section - collapsible */
        .why-section {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px dashed var(--yonca-border);
        }
        
        .why-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--yonca-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .why-content {
            font-size: 0.8rem;
            color: var(--yonca-text-secondary);
            margin-top: 8px;
            padding: 10px;
            background: var(--yonca-background);
            border-radius: 8px;
            line-height: 1.5;
        }
        
        /* Confidence indicator */
        .confidence-bar {
            height: 4px;
            background: var(--yonca-border);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            background: var(--yonca-primary);
            border-radius: 2px;
            transition: width 0.3s ease;
        }
    </style>
    """


def get_chat_css() -> str:
    """CSS for WhatsApp/Telegram-like chat bubbles."""
    return """
    <style>
        /* Chat container */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 16px 0;
        }
        
        /* Chat bubble base */
        .chat-bubble {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 18px;
            font-size: 0.9rem;
            line-height: 1.4;
            position: relative;
        }
        
        /* User message (right side, green) */
        .chat-bubble.user {
            background: var(--yonca-chat-user);
            color: var(--yonca-text-primary);
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        /* Bot message (left side, white/dark) */
        .chat-bubble.bot {
            background: var(--yonca-chat-bot);
            color: var(--yonca-text-primary);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 2px var(--yonca-shadow);
        }
        
        /* Message timestamp */
        .chat-time {
            font-size: 0.7rem;
            color: var(--yonca-text-secondary);
            margin-top: 4px;
            text-align: right;
        }
        
        /* Typing indicator */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 10px 14px;
            background: var(--yonca-chat-bot);
            border-radius: 18px;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--yonca-text-secondary);
            border-radius: 50%;
            animation: typing 1s infinite;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 100% { opacity: 0.3; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1); }
        }
        
        /* Chat input area */
        .chat-input-area {
            display: flex;
            gap: 8px;
            padding: 12px;
            background: var(--yonca-card-bg);
            border-top: 1px solid var(--yonca-border);
            position: sticky;
            bottom: 0;
        }
        
        /* Quick reply buttons */
        .quick-replies {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }
        
        .quick-reply-btn {
            background: var(--yonca-secondary-light);
            color: var(--yonca-primary-dark);
            border: 1px solid var(--yonca-secondary);
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-reply-btn:hover {
            background: var(--yonca-primary);
            color: white;
            border-color: var(--yonca-primary);
        }
    </style>
    """


def get_fab_css() -> str:
    """CSS for the floating action button (AI Pulse)."""
    return """
    <style>
        /* Floating Action Button */
        .fab-container {
            position: fixed;
            bottom: 80px;
            right: 20px;
            z-index: 1000;
        }
        
        .fab {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--yonca-primary) 0%, var(--yonca-primary-light) 100%);
            color: white;
            border: none;
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.4);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .fab:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(46, 125, 50, 0.5);
        }
        
        .fab.pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7); }
            70% { box-shadow: 0 0 0 15px rgba(46, 125, 50, 0); }
            100% { box-shadow: 0 0 0 0 rgba(46, 125, 50, 0); }
        }
        
        /* Notification badge on FAB */
        .fab-badge {
            position: absolute;
            top: -4px;
            right: -4px;
            background: var(--yonca-critical);
            color: white;
            font-size: 0.7rem;
            font-weight: 600;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
    """


def get_timeline_css() -> str:
    """CSS for the daily routine timeline."""
    return """
    <style>
        /* Timeline container */
        .timeline {
            position: relative;
            padding-left: 24px;
        }
        
        /* Timeline line */
        .timeline::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--yonca-secondary);
        }
        
        /* Timeline item */
        .timeline-item {
            position: relative;
            padding-bottom: 20px;
        }
        
        /* Timeline dot */
        .timeline-dot {
            position: absolute;
            left: -20px;
            top: 4px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--yonca-primary);
            border: 2px solid var(--yonca-card-bg);
        }
        
        .timeline-dot.critical {
            background: var(--yonca-critical);
            animation: pulse-dot 1.5s infinite;
        }
        
        .timeline-dot.high {
            background: var(--yonca-high);
        }
        
        @keyframes pulse-dot {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.3); }
        }
        
        /* Timeline content */
        .timeline-content {
            background: var(--yonca-card-bg);
            padding: 12px 16px;
            border-radius: 12px;
            box-shadow: 0 1px 4px var(--yonca-shadow);
        }
        
        .timeline-time {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--yonca-primary);
            margin-bottom: 4px;
        }
        
        .timeline-title {
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--yonca-text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .timeline-desc {
            font-size: 0.8rem;
            color: var(--yonca-text-secondary);
            margin-top: 4px;
        }
        
        .timeline-duration {
            font-size: 0.75rem;
            color: var(--yonca-text-secondary);
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }
    </style>
    """


def get_profile_card_css() -> str:
    """CSS for the farm profile overview card."""
    return """
    <style>
        /* Profile overview card */
        .profile-card {
            background: linear-gradient(135deg, var(--yonca-primary) 0%, var(--yonca-primary-light) 100%);
            color: white;
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 16px;
        }
        
        .profile-header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .profile-icon {
            font-size: 3rem;
            background: rgba(255,255,255,0.2);
            width: 64px;
            height: 64px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .profile-name {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .profile-type {
            font-size: 0.85rem;
            opacity: 0.9;
        }
        
        /* Profile stats grid */
        .profile-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .stat-item {
            background: rgba(255,255,255,0.15);
            padding: 10px 12px;
            border-radius: 12px;
        }
        
        .stat-label {
            font-size: 0.75rem;
            opacity: 0.85;
        }
        
        .stat-value {
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 2px;
        }
        
        /* Alert badge */
        .alert-badge {
            background: var(--yonca-critical);
            color: white;
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 0.8rem;
            margin-top: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
    </style>
    """


def get_scenario_switcher_css() -> str:
    """CSS for scenario selection buttons."""
    return """
    <style>
        /* Scenario switcher */
        .scenario-switcher {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 12px 0;
            -webkit-overflow-scrolling: touch;
        }
        
        .scenario-btn {
            flex-shrink: 0;
            padding: 12px 16px;
            border-radius: 12px;
            border: 2px solid var(--yonca-secondary);
            background: var(--yonca-card-bg);
            color: var(--yonca-text-primary);
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            min-width: 80px;
        }
        
        .scenario-btn:hover {
            border-color: var(--yonca-primary);
            background: var(--yonca-secondary-light);
        }
        
        .scenario-btn.active {
            border-color: var(--yonca-primary);
            background: var(--yonca-primary);
            color: white;
        }
        
        .scenario-icon {
            font-size: 1.5rem;
        }
        
        .scenario-label {
            font-size: 0.75rem;
            font-weight: 500;
        }
    </style>
    """


def get_all_styles() -> str:
    """Combine all CSS styles into a single string, including theme variables."""
    return (
        get_theme_css_variables() +
        get_mobile_container_css() +
        get_header_css() +
        get_card_css() +
        get_chat_css() +
        get_fab_css() +
        get_timeline_css() +
        get_profile_card_css() +
        get_scenario_switcher_css()
    )


# ============= HTML COMPONENT BUILDERS =============

def render_header(title: str, subtitle: str, icon: str = "🌿") -> str:
    """Render the app header HTML."""
    return f"""
    <div class="app-header">
        <div class="header-icon">{icon}</div>
        <h1>{title}</h1>
        <div class="subtitle">{subtitle}</div>
    </div>
    """


def render_insight_card(
    title: str,
    description: str,
    action: str,
    priority: str,
    why_title: str = "",
    why_content: str = "",
    confidence: float = 0.85,
    time_slot: str = ""
) -> str:
    """Render an insight card HTML."""
    priority_class = priority.lower()
    priority_labels = {
        "critical": "KRİTİK",
        "high": "YÜKSƏK",
        "medium": "ORTA",
        "low": "AŞAĞI",
    }
    
    time_html = f'<div style="font-size:0.8rem;color:var(--yonca-text-secondary);margin-bottom:8px;">⏰ {time_slot}</div>' if time_slot else ""
    
    why_html = ""
    if why_title and why_content:
        why_html = f"""
        <div class="why-section">
            <div class="why-title">❓ {why_title}</div>
            <div class="why-content">{why_content}</div>
        </div>
        """
    
    return f"""
    <div class="insight-card {priority_class}">
        <div class="card-title">
            {title}
            <span class="priority-badge {priority_class}">{priority_labels.get(priority_class, priority)}</span>
        </div>
        {time_html}
        <div class="card-description">{description}</div>
        <div class="card-action">
            <div class="card-action-title">📋 Tövsiyə olunan addım:</div>
            {action}
        </div>
        {why_html}
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {confidence * 100}%;"></div>
        </div>
    </div>
    """


def render_chat_bubble(message: str, is_user: bool, timestamp: str = "") -> str:
    """Render a chat bubble HTML."""
    bubble_class = "user" if is_user else "bot"
    time_html = f'<div class="chat-time">{timestamp}</div>' if timestamp else ""
    
    return f"""
    <div class="chat-bubble {bubble_class}">
        {message}
        {time_html}
    </div>
    """


def render_timeline_item(
    time: str,
    title: str,
    description: str,
    icon: str,
    duration: int,
    priority: str = "medium"
) -> str:
    """Render a timeline item HTML."""
    dot_class = priority.lower() if priority.lower() in ["critical", "high"] else ""
    
    return f"""
    <div class="timeline-item">
        <div class="timeline-dot {dot_class}"></div>
        <div class="timeline-content">
            <div class="timeline-time">{time}</div>
            <div class="timeline-title">{icon} {title}</div>
            <div class="timeline-desc">{description}</div>
            <div class="timeline-duration">⏱️ {duration} dəqiqə</div>
        </div>
    </div>
    """


def render_profile_card(
    name: str,
    icon: str,
    farm_type: str,
    region: str,
    area: float,
    stats: list[tuple[str, str]],
    alert: str = ""
) -> str:
    """Render the farm profile overview card."""
    stats_html = "".join([
        f'<div class="stat-item"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>'
        for label, value in stats
    ])
    
    alert_html = f'<div class="alert-badge">⚠️ {alert}</div>' if alert else ""
    
    return f"""
    <div class="profile-card">
        <div class="profile-header">
            <div class="profile-icon">{icon}</div>
            <div>
                <div class="profile-name">{name}</div>
                <div class="profile-type">{farm_type} • {region}</div>
            </div>
        </div>
        <div class="profile-stats">
            {stats_html}
            <div class="stat-item"><div class="stat-label">Sahə</div><div class="stat-value">{area} ha</div></div>
        </div>
        {alert_html}
    </div>
    """
