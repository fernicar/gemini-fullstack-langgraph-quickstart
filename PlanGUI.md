# TINS Agent PySide6 GUI

## Description

This document outlines the plan for a new PySide6-based Graphical User Interface (GUI) for the TINS Agent. This GUI aims to replace the existing React frontend and will interact directly with the LangGraph backend. The development will draw inspiration from the TINS philosophy of creating straightforward, effective tools and the structural example of `best_gui.py`.

## Functionality

### Core Features

*   **User Input Area:** A dedicated space for users to type their research queries.
*   **Effort Control:** A dropdown menu (e.g., Low, Medium, High) to control the agent's research "Effort." This will translate to backend parameters like `initial_search_query_count` and `max_research_loops`.
*   **Model Selection:** A dropdown menu to select the desired Gemini model for the agent.
*   **Chat Display Area:** A panel to display the history of the conversation, including user queries and the AI's responses.
*   **Activity Timeline:** A real-time log display showing the backend agent's processing steps (e.g., "Generating File Paths," "Reading File," "Reflection," "Finalizing Answer").
*   **Action Buttons:**
    *   **Search/Stop:** A button to submit the current query or stop an ongoing query.
    *   **New Search:** A button to clear the current session (chat, timeline, input fields) and start fresh.
    *   **Copy AI Message:** A button or context menu option to easily copy the content of an AI's message.

### User Interface (UI)

The main application window will be built using `QMainWindow`. Resizable panels will be implemented using `QSplitter` to allow users to customize their workspace, similar to the layout in `best_gui.py`.

*   **Main Window Layout:**
    *   A possible layout could be a vertical splitter:
        *   **Top Pane (Chat & Activity):** A horizontal splitter dividing this pane into:
            *   **Left: Chat Display Area.**
            *   **Right: Activity Timeline.**
        *   **Bottom Pane (Input & Controls):**
            *   User input area.
            *   Controls for Effort, Model, and action buttons.
    *   Alternatively, a left/right main splitter with chat/activity on one side and input/controls on the other.

*   **Input Area:**
    *   A `QTextEdit` widget will be used for multi-line user query input, providing ample space for detailed questions.

*   **Controls:**
    *   `QComboBox` widgets for "Effort" (e.g., items: "Low", "Medium", "High") and "Model" selection (e.g., items: "gemini-1.5-flash", "gemini-1.5-pro").
    *   `QPushButton` for "Search" (which toggles to "Stop" during processing) and "New Search."

*   **Chat Display:**
    *   A `QTextBrowser` will be used to display the conversation history. This widget supports rich text (HTML subset), which can be used to format AI messages (e.g., render Markdown if feasible, or at least bolding/italics). User messages will be displayed as plain text.

*   **Activity Timeline:**
    *   A `QListWidget` or a read-only `QTextEdit` will display a chronological log of agent activities. This display will update in real-time as events are received from the backend. `QListWidget` might be better for structured, itemized log entries.

### Behavior Specifications & User Flows

1.  **Initial State:**
    *   The GUI opens with an empty input field.
    *   The "Effort" and "Model" dropdowns are set to default values.
    *   The "Search" button is enabled. The "Stop" functionality (if part of the same button) is disabled.
    *   The "New Search" button is enabled.
    *   Chat display and Activity Timeline are empty or show a welcome message.

2.  **User Initiates Search:**
    *   User types a query into the input `QTextEdit`.
    *   User selects desired "Effort" and "Model" from the `QComboBox` widgets.
    *   User clicks the "Search" button.
    *   The UI updates:
        *   The user's query is appended to the Chat Display.
        *   The "Search" button's text changes to "Stop," and it becomes the active control for halting the process.
        *   The input `QTextEdit` might become read-only or disabled.
        *   The Activity Timeline displays an initial status like "Processing query..." or "Connecting to backend...".

3.  **Backend Processing & Streaming Updates:**
    *   As the backend agent processes the query, it streams updates.
    *   Each update (e.g., "Generating File Paths," "Reading File," "Reflection") is appended to the Activity Timeline in real-time.
    *   Intermediate results or thoughts from the agent might also be streamed to the Chat Display (if the backend supports this).

4.  **Search Completion:**
    *   When the backend completes the research, the final answer is displayed in the Chat Display.
    *   The "Stop" button reverts to "Search" and is re-enabled for a new query.
    *   The input `QTextEdit` is re-enabled (if it was disabled).
    *   The Activity Timeline shows a "Completed" or "Finalizing Answer" status.

5.  **"Stop" Button Action:**
    *   If the user clicks "Stop" while a query is processing:
        *   The GUI attempts to send a signal to the backend to halt the current operation.
        *   Locally, the GUI might stop listening for further updates for that query.
        *   The UI is reset to a state where a new query can be initiated (e.g., "Stop" button reverts to "Search", input field enabled).
        *   Activity Timeline shows "Search stopped by user."

6.  **"New Search" Button Action:**
    *   User clicks the "New Search" button.
    *   The Chat Display is cleared.
    *   The Activity Timeline is cleared.
    *   The user input `QTextEdit` is cleared.
    *   "Effort" and "Model" controls are reset to their default values.
    *   If a search is in progress, it should be stopped (similar to "Stop" button action).

## Technical Implementation

*   **Main Application Class:**
    *   A class, likely named `MainWindow` or `PlanGUIMain`, will inherit from `QMainWindow`. This class will orchestrate the UI elements and interactions.

*   **Key Widgets:**
    *   `QTextEdit`: For user query input and potentially for the Activity Timeline (if not `QListWidget`).
    *   `QTextBrowser`: For the Chat Display, allowing rich text formatting.
    *   `QComboBox`: For "Effort" and "Model" selection.
    *   `QPushButton`: For "Search/Stop" and "New Search" actions.
    *   `QSplitter`: For creating resizable panels in the layout.
    *   `QStatusBar`: Optionally, for displaying status messages or brief error notifications.

*   **Layouts:**
    *   `QVBoxLayout`, `QHBoxLayout`, and potentially `QGridLayout` will be used to arrange widgets within panes and the main window.

*   **Backend Communication:**
    *   **Method:** The GUI will use HTTP client libraries in Python (e.g., `httpx`, `requests`) to communicate with the LangGraph backend. It will specifically target an endpoint like `/agent/stream` (or as defined by the backend) that supports streaming responses.
    *   **Asynchronous Operations:** To keep the GUI responsive while waiting for backend responses, network communication will be handled in a separate thread using `QThread` and signals/slots for updating the UI.
        *   A worker `QObject` will be moved to a `QThread`. This worker will handle the network request and emit signals with data received from the backend.
        *   The main GUI thread will connect to these signals to update the `QTextBrowser` (Chat Display) and `QListWidget`/`QTextEdit` (Activity Timeline).
    *   **Data Sent to Backend:**
        *   User query (string).
        *   Effort level (e.g., "Low", "Medium", "High") which the GUI will translate into appropriate backend parameters (e.g., `initial_search_query_count`, `max_research_loops`).
        *   Selected model name (string).
    *   **Data Received from Backend:**
        *   A stream of events/messages. Each event should ideally be a JSON object specifying its type (e.g., "timeline_update", "chat_message", "error") and payload.
        *   Timeline updates will be strings describing the agent's current activity.
        *   Chat messages will be the AI's responses, potentially in Markdown.

*   **State Management:**
    *   The primary UI state (e.g., current query, selected effort/model, chat history, timeline entries) will be managed as instance variables within the `MainWindow` class.
    *   Flags will be used to track states like "search_in_progress".

*   **Styling:**
    *   The application will use modern PySide6 practices.
    *   Custom styling can be applied using Qt Style Sheets (QSS) if desired, to enhance the visual appearance beyond the default platform look and feel.

## Dependencies

*   `PySide6==6.9.1` (or a similarly recent, stable version)
*   `httpx` (for asynchronous HTTP requests)
*   `httpx[http2]` (if HTTP/2 is used by the backend)
*   Potentially `websockets` if the backend streaming protocol is WebSocket-based instead of HTTP streaming. (Assuming HTTP streaming for now based on LangGraph examples).

## Input/Output (from GUI Perspective)

*   **User Inputs:**
    *   Text entered into the query `QTextEdit`.
    *   Selections made in the "Effort" and "Model" `QComboBox` widgets.
    *   Clicks on "Search/Stop" and "New Search" `QPushButton` widgets.
*   **GUI Outputs (to Backend):**
    *   HTTP requests (likely POST) to the backend API endpoint.
    *   Payload will include the user query, effort parameters, and model name.
*   **GUI Receives (from Backend):**
    *   Streaming HTTP responses.
    *   JSON objects or Server-Sent Events (SSE) containing:
        *   Timeline update strings.
        *   AI response messages (potentially Markdown).
        *   Error messages.
*   **GUI Displays:**
    *   User queries and AI responses in the Chat Display.
    *   Agent activities in the Activity Timeline.
    *   Error messages (e.g., in the Chat Display, a status bar, or a dialog box).

## Error Handling (Conceptual)

*   **Backend Errors:**
    *   Errors reported by the backend (e.g., API errors, processing failures) will be displayed in the Chat Display, possibly formatted distinctly (e.g., red text).
    *   A message might also appear in a `QStatusBar`.
*   **Connection Errors:**
    *   If the GUI cannot connect to the backend (e.g., server down, network issue), an error message will be displayed prominently (e.g., in the Chat Display or a modal dialog).
    *   The UI should revert to a safe state (e.g., allow retrying the connection or modifying backend URL if applicable).
*   **Streaming Errors:**
    *   If the stream is interrupted, an error message should be shown. The GUI should handle this gracefully, perhaps by attempting to reconnect or by finalizing the session with an error status.

This plan provides a comprehensive guide for the development of the `main.py` PySide6 GUI.
It aligns with the TINS philosophy by aiming for a functional and user-centric interface that leverages the capabilities of the LangGraph backend.
