# Engine Rules: Graph & UI Integration

## 1. Graph Structure & Tags
*   **Visualizer/Response Node:** The node responsible for the final user response MUST be tagged with `["final_response"]`.
    ```python
    graph.add_node("visualizer", visualizer_node.with_config(tags=["final_response"]))
    ```
*   **Streaming Support:** The graph must be compile-able and runnable with `stream_mode=["updates", "messages"]`.

## 2. State Management
*   **Input/Output:** Nodes should modify state keys cleanly.
*   **Artifacts:** File paths or image references in state should be ready for the UI to consume via State-to-Element mapping.

## 3. Custom Events
*   **Progress Reporting:** Long-running nodes (e.g., simulations, agronomy checks) should emit custom events if possible, or update state frequently to allow "updates" stream to show progress.

## 4. Error Handling
*   **Graceful Failure:** Graph execution should catch internal errors and return a structured error state rather than raising exceptions that crash the client stream.
