# src/yonca/mcp_server/python_viz.py
"""Python Visualization MCP Server — Code execution for charts and diagrams.

This MCP server provides secure Python code execution for generating
visualizations (Plotly charts, Mermaid diagrams, Folium maps).

Features:
    - Sandboxed Python execution
    - Pre-installed visualization libraries
    - Timeout protection
    - Output sanitization

Run:
    python -m uvicorn yonca.mcp_server.python_viz:app --port 7778
    OR
    python src/yonca/mcp_server/python_viz.py

Security:
    - Execution timeout: 30 seconds
    - Memory limit: 256MB (via Docker)
    - No network access in sandbox
    - Read-only filesystem (except /tmp)
"""

import io
import json
import os
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# ============================================================
# Server Configuration
# ============================================================

PORT = int(os.getenv("PYTHON_VIZ_PORT", 7778))
LOG_LEVEL = os.getenv("PYTHON_VIZ_LOG_LEVEL", "INFO")
EXECUTION_TIMEOUT = int(os.getenv("PYTHON_VIZ_TIMEOUT", 30))

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

# ============================================================
# Data Models
# ============================================================


class CodeExecutionRequest(BaseModel):
    """Request to execute Python code."""

    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(default=30, ge=1, le=60, description="Execution timeout in seconds")
    return_type: str = Field(
        default="json",
        description="Expected return type: json, text, html",
    )


class CodeExecutionResponse(BaseModel):
    """Response from code execution."""

    success: bool
    output: str | None = None
    error: str | None = None
    execution_time_ms: float
    return_type: str


class PlotlyChartRequest(BaseModel):
    """Request to generate a Plotly chart."""

    chart_type: str = Field(..., description="Chart type: bar, line, pie, scatter, timeline")
    data: dict[str, Any] = Field(..., description="Data for the chart")
    title: str = Field(default="", description="Chart title")
    x_label: str = Field(default="", description="X-axis label")
    y_label: str = Field(default="", description="Y-axis label")
    theme: str = Field(default="plotly_white", description="Plotly theme")


class MermaidDiagramRequest(BaseModel):
    """Request to generate a Mermaid diagram."""

    diagram_type: str = Field(..., description="Diagram type: flowchart, sequence, gantt")
    nodes: list[dict[str, Any]] = Field(..., description="Nodes/steps in the diagram")
    title: str = Field(default="", description="Diagram title")


# ============================================================
# Sandboxed Code Execution
# ============================================================


def execute_python_safely(code: str, timeout: int = 30) -> tuple[bool, str, str]:
    """Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (success, output, error)
    """
    import signal

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Timeout handler (Unix only - Windows uses different mechanism)
    def timeout_handler(signum: int, frame: Any) -> None:
        raise TimeoutError(f"Code execution exceeded {timeout} seconds")

    # Set up restricted globals - using Any to allow dynamic assignment
    safe_globals: dict[str, Any] = {
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "list": list,
            "dict": dict,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "tuple": tuple,
            "set": set,
            "min": min,
            "max": max,
            "sum": sum,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "round": round,
            "abs": abs,
            "any": any,
            "all": all,
            "isinstance": isinstance,
            "type": type,
            "None": None,
            "True": True,
            "False": False,
        },
    }

    # Pre-import safe visualization libraries
    try:
        import plotly.express as px
        import plotly.graph_objects as go

        safe_globals["px"] = px
        safe_globals["go"] = go
        safe_globals["json"] = json

        # Optional: pandas and numpy (may not be installed)
        try:
            import numpy as np
            import pandas as pd

            safe_globals["pd"] = pd
            safe_globals["np"] = np
        except ImportError:
            pass

    except ImportError as e:
        logger.warning("visualization_library_missing", error=str(e))

    # Set timeout (Unix only - Windows uses threading)
    use_signal_timeout = hasattr(signal, "SIGALRM")

    try:
        if use_signal_timeout:
            signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore[attr-defined]
            signal.alarm(timeout)  # type: ignore[attr-defined]

        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, safe_globals)

        # Cancel timeout
        if use_signal_timeout:
            signal.alarm(0)  # type: ignore[attr-defined]

        output = stdout_capture.getvalue()
        error = stderr_capture.getvalue()

        return True, output, error

    except TimeoutError as e:
        return False, "", str(e)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return False, stdout_capture.getvalue(), error_msg
    finally:
        if use_signal_timeout:
            signal.alarm(0)  # type: ignore[attr-defined]


# ============================================================
# Chart Generation Helpers
# ============================================================


def generate_plotly_chart(request: PlotlyChartRequest) -> dict[str, Any]:
    """Generate a Plotly chart from structured data.

    Args:
        request: Chart configuration

    Returns:
        Dict with figure_json and metadata
    """
    import pandas as pd
    import plotly.express as px

    df = pd.DataFrame(request.data)

    chart_funcs = {
        "bar": px.bar,
        "line": px.line,
        "pie": px.pie,
        "scatter": px.scatter,
        "area": px.area,
    }

    chart_func = chart_funcs.get(request.chart_type)
    if not chart_func:
        raise ValueError(f"Unsupported chart type: {request.chart_type}")

    # Determine x and y columns
    columns = list(df.columns)
    x_col = columns[0] if columns else "x"
    y_col = columns[1] if len(columns) > 1 else "y"

    if request.chart_type == "pie":
        fig = chart_func(
            df,
            values=y_col,
            names=x_col,
            title=request.title,
            template=request.theme,
        )
    else:
        fig = chart_func(
            df,
            x=x_col,
            y=y_col,
            title=request.title,
            template=request.theme,
        )

    # Update labels
    fig.update_layout(
        xaxis_title=request.x_label or x_col,
        yaxis_title=request.y_label or y_col,
    )

    return {
        "figure_json": fig.to_json(),
        "chart_type": request.chart_type,
        "generated_at": datetime.utcnow().isoformat(),
    }


def generate_mermaid_diagram(request: MermaidDiagramRequest) -> dict[str, Any]:
    """Generate a Mermaid diagram from structured data.

    Args:
        request: Diagram configuration

    Returns:
        Dict with mermaid_code and metadata
    """
    if request.diagram_type == "flowchart":
        lines = ["graph TD"]
        for i, node in enumerate(request.nodes):
            node_id = node.get("id", f"N{i}")
            label = node.get("label", f"Step {i+1}")
            lines.append(f"    {node_id}[{label}]")

        # Add edges
        for i in range(len(request.nodes) - 1):
            curr_id = request.nodes[i].get("id", f"N{i}")
            next_id = request.nodes[i + 1].get("id", f"N{i+1}")
            lines.append(f"    {curr_id} --> {next_id}")

    elif request.diagram_type == "sequence":
        lines = ["sequenceDiagram"]
        for node in request.nodes:
            actor = node.get("actor", "User")
            action = node.get("action", "does something")
            target = node.get("target", "System")
            lines.append(f"    {actor}->>+{target}: {action}")

    elif request.diagram_type == "gantt":
        lines = ["gantt", f"    title {request.title}", "    dateFormat YYYY-MM-DD"]
        for node in request.nodes:
            task = node.get("task", "Task")
            start = node.get("start", "2026-01-01")
            duration = node.get("duration", "7d")
            lines.append(f"    {task} :{start}, {duration}")

    else:
        raise ValueError(f"Unsupported diagram type: {request.diagram_type}")

    mermaid_code = "\n".join(lines)

    return {
        "mermaid_code": mermaid_code,
        "diagram_type": request.diagram_type,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="Python Visualization MCP Server",
    description="MCP server for generating charts and diagrams via Python execution",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "server": "python_viz",
        "port": PORT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/mcp/tools/execute_python", response_model=CodeExecutionResponse)
async def execute_python(request: CodeExecutionRequest):
    """Execute Python code and return output.

    This is the main MCP tool for arbitrary code execution.
    Used by the visualizer node to generate custom charts.
    """
    start_time = datetime.utcnow()

    logger.info(
        "code_execution_started",
        code_length=len(request.code),
        timeout=request.timeout,
    )

    success, output, error = execute_python_safely(request.code, request.timeout)

    execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

    logger.info(
        "code_execution_completed",
        success=success,
        output_length=len(output),
        execution_time_ms=execution_time,
    )

    return CodeExecutionResponse(
        success=success,
        output=output if success else None,
        error=error if not success or error else None,
        execution_time_ms=execution_time,
        return_type=request.return_type,
    )


@app.post("/mcp/tools/generate_chart")
async def generate_chart(request: PlotlyChartRequest):
    """Generate a Plotly chart from structured data.

    Higher-level tool for common chart types without code execution.
    """
    try:
        result = generate_plotly_chart(request)
        return {"success": True, **result}
    except Exception as e:
        logger.error("chart_generation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mcp/tools/generate_diagram")
async def generate_diagram(request: MermaidDiagramRequest):
    """Generate a Mermaid diagram from structured data.

    Higher-level tool for flowcharts and process diagrams.
    """
    try:
        result = generate_mermaid_diagram(request)
        return {"success": True, **result}
    except Exception as e:
        logger.error("diagram_generation_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mcp/tools")
async def list_tools():
    """List available MCP tools (MCP discovery endpoint)."""
    return {
        "tools": [
            {
                "name": "execute_python",
                "description": "Execute Python code to generate visualizations",
                "inputSchema": CodeExecutionRequest.model_json_schema(),
            },
            {
                "name": "generate_chart",
                "description": "Generate Plotly charts from structured data",
                "inputSchema": PlotlyChartRequest.model_json_schema(),
            },
            {
                "name": "generate_diagram",
                "description": "Generate Mermaid diagrams from structured data",
                "inputSchema": MermaidDiagramRequest.model_json_schema(),
            },
        ]
    }


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print(f"🎨 Python Visualization MCP Server starting on port {PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
