from collections.abc import Callable
from typing import Any

# LangGraph's StreamWriter type (if available in current version)
# In recent LangGraph versions, this is injected via functional API or thread context.
# This helper mocks the pattern or wraps it for Agrotechnical nodes.


class ProgressStreamer:
    """Helper to stream custom events (progress, intermediate data) to UI.

    Usage in a node:
    ```python
    streamer = ProgressStreamer(writer)
    streamer.send_progress(0.5, "Scanning fields...")
    ```
    """

    def __init__(self, writer: Callable[[Any], None]):
        self.writer = writer

    def send_progress(self, percent: float, message: str):
        """Send a progress update custom event."""
        self.writer(
            {"type": "custom", "name": "progress", "data": {"percent": percent, "message": message}}
        )

    def send_map_layer(self, layer_name: str, geojson: dict):
        """Send a map layer custom event."""
        self.writer(
            {"type": "custom", "name": "map_layer", "data": {"layer": layer_name, "data": geojson}}
        )


def get_stream_writer(state: dict) -> ProgressStreamer | None:
    """Extract stream writer from state/config if available.

    Note: In LangGraph, the writer is often passed via 'writer' arg to the node
    if the node defines a 'writer' parameter and is compiled with support.

    This is a placeholder to standardize the API for 2026 nodes.
    """
    # In actual implementation, this would retrieve the writer from context
    return None
