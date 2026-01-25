# 2026 Agentic UI Standards: Integration Rules

To achieve a seamless "Antigravity-level" experience where the AI and UI move in perfect lockstep, you must treat your **LangGraph** state machine as the **Source of Truth** and **Chainlit** as a **Reactive View**.

## I. The 5 Integration Rules

### 1. The "Thread-Session" Binding
**Rule:** Every Chainlit `session_id` must map directly to a LangGraph `thread_id`.
*   **Implementation:** Store `config = {"configurable": {"thread_id": cl.user_session.get("id")}}` in the Chainlit session.
*   **Goal:** Ensures persistent conversation state across refreshes or device switches.

### 2. Triple-Mode Streaming
**Rule:** Stream **Nodes**, **Tokens**, and **Custom Events** simultaneously.
*   **Updates:** Use `stream_mode="updates"` to show active nodes ("ALİM is checking EKTİS database...").
*   **Messages:** Use `stream_mode="messages"` for real-time token delivery.
*   **Custom:** Use custom events for high-level progress updates (e.g., maps, charts).

### 3. The "Hanging Curtain" UI (Step Logic)
**Rule:** Every LangGraph Node must be wrapped in a `cl.Step` context.
*   **UX Design:**
    *   Start `cl.Step` when node starts.
    *   Collapse `cl.Step` when node finishes.
*   **Goal:** Creates professional "Chain of Thought" look without raw log overwhelm.

### 4. Final Node Tagging
**Rule:** Explicitly tag your "Response" node in the graph.
*   **Logic:** Tag final node with `tags=["final_response"]`.
*   **UI Behavior:** UI detects this tag to stop spinners and render the primary message.

### 5. State-to-Element Mapping
**Rule:** Complex state data (files, images) should not be sent as text.
*   **Strategy:** Use `cl.Message(elements=[...])` to push state changes (files/images) to sidebar/canvas.

## II. Modular UX Design Principles

*   **Deterministic Intent:** Use `cl.set_commands` for specific entry points.
*   **Async Handover:** Use `asyncio.Queue` for long-running simulations.
*   **Optimistic State:** Update UI *before* node completion for perceived speed.
