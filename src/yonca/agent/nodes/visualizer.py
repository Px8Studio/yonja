# src/yonca/agent/nodes/visualizer.py
"""Visualizer node for intelligent chart/diagram generation.

This node acts as a "reflection" step that analyzes the specialist's response
and decides if visualization would help the farmer understand the advice better.

Visualization Types:
    - Bar/Line charts: For comparisons (fertilizer ratios, yield trends)
    - Pie charts: For distributions (expenses, subsidy breakdowns)
    - Process diagrams: For SOPs (how to apply pesticide, planting steps)
    - Maps: For spatial data (field boundaries, soil zones)

Architecture:
    1. Specialist generates text advice
    2. Visualizer analyzes if visual would help
    3. If yes, calls Python MCP to generate chart
    4. Returns visualization artifact for Chainlit to render
"""

from typing import Any

import structlog

from yonca.agent.state import AgentState, UserIntent

logger = structlog.get_logger(__name__)

# ============================================================
# Visualization Triggers (Intent & Content Analysis)
# ============================================================

# Keywords that suggest visualization would be helpful (Azerbaijani)
VIZ_TRIGGERS_AZ = {
    "comparison": [
        "azaltmaq",
        "artırmaq",
        "%",
        "faiz",
        "nisbət",
        "müqayisə",
        "fərq",
        "daha çox",
        "daha az",
        "cədvəl",
        "kq/ha",
        "kg/ha",
    ],
    "timeline": [
        "gün",
        "həftə",
        "ay",
        "plan",
        "cədvəl",
        "tarix",
        "müddət",
        "zaman",
        "ardıcıllıq",
        "mərhələ",
    ],
    "spatial": [
        "sahə",
        "parsel",
        "hektar",
        "ərazi",
        "xəritə",
        "zona",
        "bölgə",
        "sərhəd",
    ],
    "process": [
        "addım",
        "mərhələ",
        "proses",
        "necə",
        "ardıcıllıq",
        "üsul",
        "qaydası",
        "tətbiq",
    ],
    "distribution": [
        "paylanma",
        "bölgü",
        "xərc",
        "subsidiya",
        "gəlir",
        "büdcə",
        "maliyyə",
    ],
}

# Intent-to-visualization mapping
INTENT_VIZ_MAP = {
    UserIntent.FERTILIZATION: "comparison",  # Fertilizer ratios → bar chart
    UserIntent.IRRIGATION: "timeline",  # Watering schedule → timeline
    UserIntent.PEST_CONTROL: "process",  # Treatment steps → flowchart
    UserIntent.HARVEST: "timeline",  # Harvest timing → calendar
    UserIntent.PLANTING: "process",  # Planting guide → steps
    UserIntent.CROP_ROTATION: "timeline",  # Rotation plan → calendar
    UserIntent.DATA_QUERY: "comparison",  # Query results → table/chart
}

# Visualization type to chart library mapping
VIZ_LIBRARY_MAP = {
    "comparison": "plotly",  # Interactive bar/line charts
    "timeline": "plotly",  # Gantt/timeline charts
    "spatial": "folium",  # Interactive maps
    "process": "mermaid",  # Flowcharts/diagrams
    "distribution": "plotly",  # Pie/donut charts
}


# ============================================================
# Visualization Decision Logic
# ============================================================


def analyze_content_for_viz(content: str) -> dict[str, float]:
    """Analyze content to determine visualization suitability.

    Args:
        content: The specialist's response text

    Returns:
        Dict of visualization type → confidence score (0-1)
    """
    content_lower = content.lower()
    scores: dict[str, float] = {}

    for viz_type, triggers in VIZ_TRIGGERS_AZ.items():
        matches = sum(1 for trigger in triggers if trigger in content_lower)
        # Normalize: 3+ matches = high confidence
        confidence = min(matches / 3, 1.0)
        if confidence > 0.3:  # Threshold
            scores[viz_type] = confidence

    return scores


def should_visualize(state: AgentState) -> tuple[bool, str | None, float]:
    """Determine if visualization would help the user.

    Decision factors:
    1. Intent type (some intents naturally need visuals)
    2. Content analysis (keywords suggest data/comparisons)
    3. Data presence (structured data in response)

    Args:
        state: Current agent state

    Returns:
        Tuple of (should_visualize, viz_type, confidence)
    """
    response = state.get("current_response", "")
    intent = state.get("intent")

    # Skip if no response
    if not response or len(response) < 50:
        return False, None, 0.0

    # 1. Check intent-based visualization
    if intent and intent in INTENT_VIZ_MAP:
        viz_type = INTENT_VIZ_MAP[intent]
        # Intent suggests visualization, check content for confirmation
        content_scores = analyze_content_for_viz(response)
        if viz_type in content_scores and content_scores[viz_type] > 0.4:
            logger.debug(
                "viz_intent_match",
                intent=intent.value,
                viz_type=viz_type,
                confidence=content_scores[viz_type],
            )
            return True, viz_type, content_scores[viz_type]

    # 2. Check content-based visualization
    content_scores = analyze_content_for_viz(response)
    if content_scores:
        # Pick highest confidence visualization type
        best_type = max(content_scores, key=lambda k: content_scores.get(k, 0.0))
        best_score = content_scores[best_type]
        if best_score > 0.5:
            logger.debug(
                "viz_content_match",
                viz_type=best_type,
                confidence=best_score,
            )
            return True, best_type, best_score

    return False, None, 0.0


# ============================================================
# Visualization Generation Prompts
# ============================================================


def build_viz_prompt(viz_type: str, content: str, intent: UserIntent | None) -> str:
    """Build prompt for Python MCP to generate visualization.

    Args:
        viz_type: Type of visualization to generate
        content: The specialist's response to visualize
        intent: User's original intent

    Returns:
        Python code generation prompt
    """
    intent_context = f"User asked about: {intent.value}" if intent else ""

    if viz_type == "comparison":
        return f"""
Analyze this agricultural advice and create a Plotly bar or line chart:

{content}

{intent_context}

Requirements:
1. Extract numerical data (percentages, amounts, comparisons)
2. Create clear labels in Azerbaijani
3. Use appropriate colors (green for positive, red for warnings)
4. Return the figure as JSON using fig.to_json()

Example output format:
```python
import plotly.express as px
data = {{"Göstərici": [...], "Dəyər": [...]}}
fig = px.bar(data, x="Göstərici", y="Dəyər", title="...")
print(fig.to_json())
```
"""
    elif viz_type == "timeline":
        return f"""
Analyze this agricultural advice and create a timeline/calendar visualization:

{content}

{intent_context}

Requirements:
1. Extract dates, durations, or periods mentioned
2. Create a Plotly timeline or Gantt chart
3. Labels in Azerbaijani
4. Return the figure as JSON

Example:
```python
import plotly.express as px
fig = px.timeline(data, x_start="Başlanğıc", x_end="Son", y="Mərhələ")
print(fig.to_json())
```
"""
    elif viz_type == "process":
        return f"""
Analyze this agricultural advice and create a process flowchart:

{content}

{intent_context}

Requirements:
1. Extract steps or stages from the advice
2. Create a Mermaid flowchart diagram
3. Labels in Azerbaijani
4. Return Mermaid markdown syntax

Example output:
```mermaid
graph TD
    A[Başlanğıc] --> B[Addım 1]
    B --> C[Addım 2]
    C --> D[Son]
```
"""
    elif viz_type == "distribution":
        return f"""
Analyze this agricultural advice and create a distribution chart:

{content}

{intent_context}

Requirements:
1. Extract categories and their proportions
2. Create a Plotly pie or donut chart
3. Labels in Azerbaijani
4. Return the figure as JSON

Example:
```python
import plotly.express as px
fig = px.pie(data, values="Məbləğ", names="Kateqoriya", title="...")
print(fig.to_json())
```
"""
    else:
        return f"""
Analyze this agricultural advice and create an appropriate visualization:

{content}

{intent_context}

Choose the best visualization type and create it using Plotly.
Return as JSON using fig.to_json().
"""


# ============================================================
# Visualizer Node
# ============================================================


async def visualizer_node(state: AgentState) -> dict[str, Any]:
    """Visualizer node for intelligent chart generation.

    Analyzes the specialist's response and decides if visualization
    would help the farmer understand the advice better.

    If visualization is needed, prepares a request for the Python MCP
    server to generate the appropriate chart/diagram.

    Args:
        state: Current agent state with specialist response

    Returns:
        State update with visualization request or None
    """
    nodes_visited = state.get("nodes_visited", []) + ["visualizer"]

    # Check if visualization would help
    should_viz, viz_type, confidence = should_visualize(state)

    if not should_viz or not viz_type:
        response = state.get("current_response", "") or ""
        logger.info(
            "visualizer_skipped",
            reason="no_visualization_needed",
            response_length=len(response),
        )
        return {
            "nodes_visited": nodes_visited,
            "visualization": None,
            "visualization_type": None,
        }

    # Get context for visualization
    content = state.get("current_response", "") or ""
    intent = state.get("intent")

    # Build visualization prompt
    viz_prompt = build_viz_prompt(viz_type, content, intent)
    viz_library = VIZ_LIBRARY_MAP.get(viz_type, "plotly")

    logger.info(
        "visualizer_triggered",
        viz_type=viz_type,
        viz_library=viz_library,
        confidence=confidence,
        intent=intent.value if intent else None,
    )

    # Return visualization request for MCP tool execution
    return {
        "nodes_visited": nodes_visited,
        "visualization_request": {
            "type": viz_type,
            "library": viz_library,
            "prompt": viz_prompt,
            "source_content": content[:500] if content else "",  # Truncate for logging
            "confidence": confidence,
        },
        "visualization": None,  # Will be populated after MCP call
        "visualization_type": viz_type,
    }


async def route_after_visualizer(state: AgentState) -> str:
    """Route after visualizer node.

    If visualization was requested, route to MCP tools.
    Otherwise, go to END.

    Args:
        state: Current agent state

    Returns:
        Next node name ("python_viz_tools" or "end")
    """
    if state.get("visualization_request"):
        return "python_viz_tools"
    return "end"


# ============================================================
# Visualization Result Handler
# ============================================================


def format_visualization_for_chainlit(
    viz_result: dict[str, Any],
    viz_type: str,
) -> dict[str, Any]:
    """Format visualization result for Chainlit rendering.

    Converts MCP tool output to Chainlit element format.

    Args:
        viz_result: Raw output from Python MCP tool
        viz_type: Type of visualization

    Returns:
        Dict with Chainlit element configuration
    """
    if viz_type in ["comparison", "timeline", "distribution"]:
        # Plotly JSON → Chainlit Plotly element
        return {
            "element_type": "plotly",
            "data": viz_result.get("figure_json"),
            "name": "visualization",
            "display": "inline",
        }
    elif viz_type == "process":
        # Mermaid markdown → Chainlit Text element with code block
        return {
            "element_type": "text",
            "content": f"```mermaid\n{viz_result.get('mermaid_code')}\n```",
            "name": "process_diagram",
        }
    elif viz_type == "spatial":
        # Folium HTML → Chainlit HTML element
        return {
            "element_type": "html",
            "content": viz_result.get("map_html"),
            "name": "map",
        }
    else:
        return {
            "element_type": "text",
            "content": str(viz_result),
            "name": "raw_output",
        }
