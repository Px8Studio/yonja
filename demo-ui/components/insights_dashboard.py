# demo-ui/components/insights_dashboard.py
"""Chainlit Dashboard Components for User Insights.

Uses ONLY Chainlit-native elements to display Langfuse data:
- cl.Text for metadata display
- cl.Plotly for interactive charts (heatmap, etc.)
- cl.ElementSidebar for dashboard panel

No custom JSX needed - pure Python Chainlit components.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import chainlit as cl

if TYPE_CHECKING:
    from services.langfuse_insights import DailyActivity, ResponseMetadata, UserInsights


# ============================================================
# Per-Message Response Metadata (Expandable)
# ============================================================


def format_response_metadata(metadata: ResponseMetadata) -> str:
    """Format response metadata as collapsible markdown text.

    This appears under each AI response when expanded.
    """
    # Build thinking process description
    if metadata.nodes_executed:
        _thinking_steps = " → ".join(metadata.nodes_executed)
    else:
        _thinking_steps = "Direct response"

    # Determine speed indicator
    if metadata.latency_ms < 500:
        speed_emoji = "⚡"
        _speed_label = "Very Fast"
    elif metadata.latency_ms < 1500:
        speed_emoji = "🚀"
        _speed_label = "Fast"
    elif metadata.latency_ms < 3000:
        speed_emoji = "⏱️"
        _speed_label = "Normal"
    else:
        speed_emoji = "🐢"
        _speed_label = "Slow"

    # Format the metadata block
    metadata_text = f"""
<details>
<summary>📊 <em>Details</em></summary>

| | |
|:--|:--|
| {speed_emoji} Time | {metadata.latency_display} |
| 📝 Tokens | {metadata.tokens_display} |
| 🤖 Model | `{metadata.model}` |

<sub>[Trace](http://localhost:3001/trace/{metadata.trace_id})</sub>

</details>
"""
    return metadata_text.strip()


async def add_response_metadata_element(
    message: cl.Message,
    metadata: ResponseMetadata,
) -> None:
    """Add expandable metadata element to a message.

    Args:
        message: The Chainlit message to add metadata to
        metadata: The response metadata from Langfuse
    """
    metadata_text = format_response_metadata(metadata)

    # Create a Text element with the metadata
    text_element = cl.Text(
        name="response_details",
        content=metadata_text,
        display="inline",
    )

    # Add to message elements
    if message.elements is None:
        message.elements = []
    message.elements.append(text_element)

    await message.update()


# ============================================================
# Activity Heatmap (GitHub-style)
# ============================================================


def create_activity_heatmap(
    daily_activity: list[DailyActivity],
    title: str = "🗓️ Activity Overview",
) -> cl.Plotly:
    """Create a GitHub-style activity heatmap using Plotly.

    Shows last 90 days of activity with intensity coloring.

    Args:
        daily_activity: List of DailyActivity objects
        title: Chart title

    Returns:
        Chainlit Plotly element
    """
    import plotly.graph_objects as go

    if not daily_activity:
        # Empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No activity data yet. Start chatting to build your history!",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        fig.update_layout(
            height=150,
            margin=dict(l=20, r=20, t=40, b=20),
            title=dict(text=title, x=0.5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return cl.Plotly(name="activity_heatmap", figure=fig, display="inline")

    # Prepare data for heatmap
    # Organize into weeks (columns) and days (rows, Mon=0 to Sun=6)
    weeks_data: dict[int, dict[int, DailyActivity]] = {}

    # Find the start date (beginning of the week containing the oldest date)
    oldest = min(a.date for a in daily_activity)
    start_of_week = oldest - timedelta(days=oldest.weekday())

    for activity in daily_activity:
        # Calculate week number from start
        days_since_start = (activity.date - start_of_week).days
        week_num = days_since_start // 7
        day_of_week = activity.date.weekday()

        if week_num not in weeks_data:
            weeks_data[week_num] = {}
        weeks_data[week_num][day_of_week] = activity

    # Build the heatmap matrix
    num_weeks = max(weeks_data.keys()) + 1 if weeks_data else 1

    z_data = []  # Intensity values
    text_data = []  # Hover text

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for day_idx in range(7):
        row_z = []
        row_text = []

        for week_idx in range(num_weeks):
            activity = weeks_data.get(week_idx, {}).get(day_idx)

            if activity:
                row_z.append(activity.intensity)
                date_str = activity.date.strftime("%b %d")
                row_text.append(
                    f"{date_str}<br>"
                    f"{activity.interaction_count} interactions<br>"
                    f"{activity.total_tokens:,} tokens"
                )
            else:
                row_z.append(0)
                row_text.append("No data")

        z_data.append(row_z)
        text_data.append(row_text)

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            text=text_data,
            hovertemplate="%{text}<extra></extra>",
            colorscale=[
                [0, "#161b22"],  # Level 0 - No activity (dark)
                [0.25, "#0e4429"],  # Level 1 - Low
                [0.5, "#006d32"],  # Level 2 - Medium
                [0.75, "#26a641"],  # Level 3 - High
                [1.0, "#39d353"],  # Level 4 - Very high
            ],
            showscale=False,
            xgap=3,
            ygap=3,
        )
    )

    # Week labels (show month at start of each month)
    week_labels = []
    for week_idx in range(num_weeks):
        week_start = start_of_week + timedelta(weeks=week_idx)
        if week_start.day <= 7:  # First week of month
            week_labels.append(week_start.strftime("%b"))
        else:
            week_labels.append("")

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        height=180,
        margin=dict(l=40, r=20, t=50, b=20),
        yaxis=dict(
            ticktext=day_names,
            tickvals=list(range(7)),
            tickfont=dict(size=10),
            showgrid=False,
        ),
        xaxis=dict(
            ticktext=week_labels,
            tickvals=list(range(num_weeks)),
            tickfont=dict(size=10),
            showgrid=False,
            side="top",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return cl.Plotly(name="activity_heatmap", figure=fig, display="inline")


# ============================================================
# Usage Stats Cards
# ============================================================


def format_dashboard_summary(
    insights: UserInsights,
    alem_persona: dict | None = None,
    expertise_areas: list[str] | None = None,
) -> str:
    """Format the main dashboard summary as compact, GitHub-style markdown.

    Shows "how ALEM sees you" - combining Langfuse metrics with persona data.

    Args:
        insights: UserInsights from Langfuse
        alem_persona: ALEM persona dictionary from session
        expertise_areas: Detected expertise areas from profile

    Returns:
        Markdown string for display
    """
    if insights.total_interactions == 0 and not alem_persona:
        return """
*🌱 New user — ALEM is learning about you...*
"""

    # === ALEM MIRROR: WHO YOU ARE ===
    mirror_lines = []

    if alem_persona:
        # Farmer identity
        crop = alem_persona.get("crop_type", "N/A")
        region = alem_persona.get("region", "N/A")
        experience = alem_persona.get("experience_level", "N/A")
        farm_size = alem_persona.get("farm_size_ha", 0)

        # Experience emoji
        if experience == "expert":
            exp_emoji = "🎓"
        elif experience == "intermediate":
            exp_emoji = "🌾"
        else:
            exp_emoji = "🌱"

        # Farm size category
        if farm_size >= 30:
            size_emoji = "🏭"
            size_label = "Large"
        elif farm_size >= 10:
            size_emoji = "🏘️"
            size_label = "Medium"
        else:
            size_emoji = "🏡"
            size_label = "Small"

        mirror_lines.append(f"**🌿 {crop}** fermer · {region}")
        mirror_lines.append(
            f"{exp_emoji} {experience.title()} · {size_emoji} {size_label} ({farm_size:.1f} ha)"
        )

        # Expertise areas (auto-detected)
        if expertise_areas:
            expertise_labels = {
                "cotton": "Pambıq",
                "wheat": "Taxıl",
                "orchard": "Meyvə",
                "vegetable": "Tərəvəz",
                "livestock": "Heyvandarlıq",
                "advanced": "Qabaqcıl",
                "general": "Ümumi",
            }
            skills = [expertise_labels.get(e, e) for e in expertise_areas[:3]]
            mirror_lines.append(f"🎯 {' · '.join(skills)}")

    # === ACTIVITY METRICS (GitHub-style compact) ===
    if insights.total_interactions > 0:
        # Streak emoji
        if insights.streak_days >= 7:
            streak_emoji = "🔥"
        elif insights.streak_days >= 3:
            streak_emoji = "⭐"
        else:
            streak_emoji = "📅"

        # Compact metric line (GitHub contributions style)
        metrics = f"{insights.total_interactions:,} sual · {insights.total_sessions:,} söhbət · {streak_emoji} {insights.streak_days}d"
        mirror_lines.append(metrics)

        # Member since (subtle)
        if insights.first_interaction:
            member_since = insights.first_interaction.strftime("%b %Y")
            mirror_lines.append(f"<sub>Since {member_since}</sub>")

    # Build final compact layout
    return "\n\n".join(mirror_lines) if mirror_lines else "*No data yet*"


def format_daily_breakdown(
    date: datetime,
    traces: list[dict],
) -> str:
    """Format traces for a specific day as markdown.

    Args:
        date: The date being displayed
        traces: List of traces from Langfuse

    Returns:
        Markdown string for display
    """
    date_str = date.strftime("%A, %B %d, %Y")

    if not traces:
        return f"""
### 📅 {date_str}

*No interactions on this day.*
"""

    # Build interaction list
    interaction_items = []

    for trace in traces[:10]:  # Limit to 10
        timestamp = datetime.fromisoformat(trace["timestamp"].replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M")

        # Get summary (input or name)
        summary = trace.get("input", trace.get("name", "Interaction"))
        if isinstance(summary, dict):
            summary = summary.get("messages", [{}])[0].get("content", "Interaction")[:50]
        elif isinstance(summary, str):
            summary = summary[:50]

        if len(str(summary)) >= 50:
            summary = str(summary)[:47] + "..."

        tokens = trace.get("totalTokens", 0) or 0

        interaction_items.append(f"- **{time_str}** — {summary} ({tokens:,} tokens)")

    interactions_md = "\n".join(interaction_items)

    remaining = len(traces) - 10
    if remaining > 0:
        interactions_md += f"\n\n*...and {remaining} more interactions*"

    return f"""
### 📅 {date_str}

**{len(traces)} interactions**

{interactions_md}
"""


# ============================================================
# Full Dashboard Assembly
# ============================================================


async def render_dashboard_sidebar(
    insights: UserInsights,
    alem_persona: dict | None = None,
    expertise_areas: list[str] | None = None,
) -> None:
    """Render the full dashboard in Chainlit's sidebar.

    This is the SECONDARY welcome element (non-intrusive analytics).
    Shows "how ALEM sees you" — combining Langfuse metrics with persona/farm data.
    Loads in background while main welcome message appears in chat.

    Companion to: send_dashboard_welcome() in app.py (primary greeting)

    Args:
        insights: UserInsights from Langfuse
        alem_persona: ALEM persona dictionary from session (optional)
        expertise_areas: Detected expertise areas (optional)
    """
    elements = []

    # 1. ALEM Mirror: WHO YOU ARE + Activity (compact)
    summary_text = format_dashboard_summary(insights, alem_persona, expertise_areas)
    elements.append(
        cl.Text(
            name="alem_mirror",
            content=summary_text,
            display="inline",
        )
    )

    # 2. Activity heatmap (only if there's data)
    if insights.daily_activity:
        heatmap = create_activity_heatmap(insights.daily_activity, title="")
        elements.append(heatmap)

        # Legend for heatmap (subtle)
        legend_text = "<sub>🟫 Less → 🟩 More</sub>"
        elements.append(
            cl.Text(
                name="heatmap_legend",
                content=legend_text,
                display="inline",
            )
        )

    # Set sidebar (compact title)
    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("🌿 ALEM Mirror")


async def update_dashboard_with_day(
    insights: UserInsights,
    selected_date: datetime,
    traces: list[dict],
) -> None:
    """Update dashboard to show drill-down for a specific day.

    Args:
        insights: Full user insights
        selected_date: The date to show details for
        traces: Traces for that day
    """
    elements = []

    # 1. Back button and summary
    summary_text = format_dashboard_summary(insights)
    elements.append(
        cl.Text(
            name="dashboard_summary",
            content=summary_text,
            display="inline",
        )
    )

    # 2. Day breakdown
    day_breakdown = format_daily_breakdown(selected_date, traces)
    elements.append(
        cl.Text(
            name="day_breakdown",
            content=day_breakdown,
            display="inline",
        )
    )

    # Set sidebar
    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("📊 Your Activity")


# ============================================================
# Quick Stats (for chat start message)
# ============================================================


def format_welcome_stats(insights: UserInsights) -> str:
    """Format a brief welcome message with stats.

    Args:
        insights: UserInsights from Langfuse

    Returns:
        Short markdown string for welcome message
    """
    if insights.total_interactions == 0:
        return "👋 Welcome! This is your first session."

    if insights.streak_days > 0:
        streak_text = f"🔥 {insights.streak_days}-day streak!"
    else:
        streak_text = "Ready to continue?"

    return (
        f"👋 Welcome back! You've had {insights.total_interactions:,} interactions. {streak_text}"
    )
