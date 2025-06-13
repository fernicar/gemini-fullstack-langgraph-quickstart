# Gemini Fullstack LangGraph Quickstart (TINS Edition)

<!-- TINS Specification v1.0 -->
<!-- ZS:PLATFORM:WEB -->
<!-- ZS:LANGUAGE:PYTHON_BACKEND,TYPESCRIPT_FRONTEND -->

## Description

This project, the Gemini Fullstack LangGraph Quickstart, demonstrates a fullstack application using a React frontend and a LangGraph-powered backend agent. The agent is designed to perform comprehensive research on a user's query by dynamically generating search terms (file paths in this modified version), reading relevant project files, reflecting on the results to identify knowledge gaps, and iteratively refining its search until it can provide a well-supported answer with citations from those files. This application serves as an example of building research-augmented conversational AI using LangGraph and Google's Gemini models, adapted to perform analysis on local project files.

## Functionality

### Core Features
*   **Backend Agent (Conceptual `model.py` - implemented in `backend/src/agent/graph.py` and supporting files):**
    1.  **Generate Initial Queries (File Paths):** Based on user input, generates a set of initial file paths to investigate using a Gemini model.
    2.  **File Reading (Simulated Web Research):** For each file path, reads the content of the specified project file.
    3.  **Reflection & Knowledge Gap Analysis:** Analyzes the gathered file contents to determine if the information is sufficient or if there are knowledge gaps. Uses a Gemini model for this reflection.
    4.  **Iterative Refinement:** If gaps are found or information is insufficient, generates follow-up file paths to read and repeats the file reading and reflection steps (up to a configured maximum).
    5.  **Finalize Answer:** Synthesizes the gathered information from files into a coherent answer, including citations (file paths), using a Gemini model.
*   **Frontend User Interface (Conceptual `main.py` - implemented in `frontend/src/App.tsx` and components):**
    *   Allows users to input research queries.
    *   Provides options to control agent "Effort" (affecting depth of file search) and "Model" (for LLM reasoning).
    *   Displays chat history of user queries and AI-generated answers.
    *   Shows a real-time `ActivityTimeline` of the backend agent's research process.
    *   Allows users to copy AI messages.
    *   Option to start a new search session.

### User Interface (UI)
(Note: This project uses a React/TypeScript frontend. This section describes the UI which corresponds to the `main.py` (GUI) role mentioned in `scuffedepoch-sysp.md`. The main UI logic is in `frontend/src/App.tsx` and its components.)

This project uses a React frontend. The UI is a single-page application with the following key components and layout:

*   **Main Application Structure (`App.tsx`):**
    *   A central, full-screen layout that hosts either the `WelcomeScreen` or the `ChatMessagesView`.
*   **Welcome Screen (`WelcomeScreen.tsx`):**
    *   Appears on initial load when no chat history exists.
    *   Displays a greeting: "Welcome." and "How can I help you today?"
    *   Includes the `InputForm` for the user's first query.
    *   Shows a footer: "Powered by Google Gemini and LangChain LangGraph."
*   **Chat Messages View (`ChatMessagesView.tsx`):**
    *   Appears once a query is submitted.
    *   Contains a scrollable area (`ScrollArea`) displaying the conversation history (user messages and AI responses).
    *   AI messages can feature an `ActivityTimeline` detailing the agent's actions.
    *   The `InputForm` is fixed at the bottom of this view for subsequent interactions.
*   **Input Form (`InputForm.tsx`):**
    *   `Textarea`: Multi-line input for the user's research query. Placeholder: "Describe the information or rules you are looking for from the project files..."
    *   `Button` ("Search" / "Stop"): Submits the query or cancels ongoing processing. Icon changes accordingly (`Send` / `StopCircle`).
    *   `Select` Dropdown ("Effort"): Allows user to choose "Low", "Medium", or "High" effort, which translates to `initial_search_query_count` and `max_research_loops` for the backend agent.
    *   `Select` Dropdown ("Model"): Allows user to choose the Gemini model for reasoning (e.g., "2.0 Flash", "2.5 Flash", "2.5 Pro").
    *   `Button` ("New Search"): Appears if chat history exists; reloads the application to start a fresh session.
*   **AI Message Display:**
    *   AI-generated answers are rendered using Markdown (`ReactMarkdown`).
    *   A "Copy" button (`Copy` icon) is provided for each AI message.
*   **Activity Timeline (`ActivityTimeline.tsx`):**
    *   A collapsible section titled "Research" within or alongside AI messages.
    *   Displays a chronological list of the backend agent's key processing steps (e.g., "Generating Search Queries", "File Reading", "Reflection", "Finalizing Answer") with icons and brief details.
    *   Shows a loading indicator (spinner icon) during active processing.

**Layout:**
*   The application is a single, centered column (`App.tsx`).
*   `WelcomeScreen` is centered on the page.
*   `ChatMessagesView` takes the main space, with messages flowing vertically and the `InputForm` docked at the bottom. Human messages and AI messages are typically aligned to opposite sides for readability.

*(Refer to `app.png` in the root directory for a visual representation of the UI.)*

### Behavior Specifications & User Flows

**User Interaction Flow:**
1.  **Greeting:** User lands on the `WelcomeScreen`.
2.  **Query Input:** User types a query into the `Textarea`, optionally selects "Effort" and "Model" via dropdowns in the `InputForm`.
3.  **Submission:** User clicks "Search" button or presses Enter (without Shift) in the `Textarea`.
4.  **Processing View:** UI transitions to `ChatMessagesView`. The user's query appears as a human message. A live `ActivityTimeline` and loading indicators (e.g., spinner in AI message placeholder) show backend processing. The "Search" button changes to a "Stop" button.
5.  **Agent Updates:** The `ActivityTimeline` updates in real-time reflecting backend steps (e.g., "Generating Search Queries", "Web Research", "Reflection").
6.  **Answer Display:** Once complete, the AI's final answer is shown in an AI message bubble. The `ActivityTimeline` for this interaction becomes static (historical). The "Stop" button reverts to "Search".
7.  **Interaction with Answer:** User can read the answer, review the timeline (expand/collapse "Research" section), and use the "Copy" button.
8.  **Follow-up/New Query:** User can enter a new query in the `InputForm` at the bottom to continue the conversation or click "New Search" button (if available) to reset and return to `WelcomeScreen`.
9.  **Cancellation:** User can click the "Stop" button during processing. This triggers `window.location.reload()`.

**Event Handling (Frontend to Backend Communication):**
*   User input (typing in `Textarea`, selecting from dropdowns) is managed by React state.
*   Submitting the `InputForm` (via button click or Enter key) triggers the `handleSubmit` function in `App.tsx`.
*   This function calls `thread.submit()` (from `@langchain/langgraph-sdk/react`) with a payload containing:
    *   The current list of messages (including the new human input).
    *   `initial_search_query_count`: Derived from the "Effort" selection (Low=1, Medium=3, High=5).
    *   `max_research_loops`: Derived from the "Effort" selection (Low=1, Medium=3, High=10).
    *   `reasoning_model`: The string value from the "Model" selection.
*   This sends the data to the LangGraph backend agent, initiating its research process.

**Backend to Frontend Communication (Streaming Updates):**
*   The frontend's `useStream` hook establishes a streaming connection with the backend agent.
*   The backend (LangGraph agent) streams events and data.
*   The `onUpdateEvent` callback in `App.tsx` processes these events (e.g., `generate_query`, `web_research`, `reflection`, `finalize_answer`) to create `ProcessedEvent` objects, updating the `processedEventsTimeline` state, which renders the live `ActivityTimeline`.
*   The `messagesKey: "messages"` configuration in `useStream` ensures that `thread.messages` state is updated when the backend stream includes a new list of messages, automatically re-rendering `ChatMessagesView`.
*   The `thread.isLoading` state variable reflects backend processing status, controlling UI loading indicators and button states.
*   Historical activities are stored with AI message IDs upon completion.

## Technical Implementation

### Architecture
The application follows a client-server architecture:
*   **Frontend (Client-Side):** A React single-page application built with Vite and TypeScript. It handles user interaction, presents data, and communicates with the backend. This corresponds to the conceptual `main.py` (GUI) role. Key files: `frontend/src/App.tsx`, `frontend/src/components/`.
*   **Backend (Server-Side):** A Python application using FastAPI to serve the API endpoints and LangGraph to define and run the research agent. This corresponds to the conceptual `model.py` (logic) role. Key files: `backend/src/agent/graph.py`, `backend/src/agent/state.py`, `backend/src/agent/app.py`.
*   **API:** The LangGraph SDK uses a combination of HTTP and WebSockets (implicitly) for streaming updates from the backend agent to the frontend. The primary interaction point is the `/agent/stream` endpoint provided by LangGraph.

*(Refer to `agent.png` in the root directory for a diagram of the backend agent's internal flow.)*

```mermaid
graph LR
    A[User Interface (React Frontend)] -- HTTP/WebSocket (Query via thread.submit) --> B(FastAPI Backend + LangGraph Agent)
    B -- HTTP/WebSocket (Streaming Updates & Final Answer via useStream) --> A
    B -- API Call (LLM for Query Gen, Reflection, Answer) --> C{Google Gemini API}
    B -- File System Read --> D[Project Files (Local)]
```

### Data Structures (Backend Agent State)
The backend LangGraph agent manages its state using TypedDicts defined in `backend/src/agent/state.py`:
```python
# Key state object passed through the graph
class OverallState(TypedDict):
    messages: Annotated[list, add_messages] # Chat history
    search_query: Annotated[list, operator.add] # List of file paths searched
    web_research_result: Annotated[list, operator.add] # List of contents read from files
    sources_gathered: Annotated[list, operator.add] # Detailed info about files read (e.g., {'type': 'file', 'source': 'path/to/file', 'content': '...', 'id': 0})
    initial_search_query_count: int # Number of initial queries to generate
    max_research_loops: int # Maximum iterations for the research loop
    research_loop_count: int # Current iteration count of the research loop
    reasoning_model: str # Name of the LLM model to use for reasoning

# State for reflection node
class ReflectionState(TypedDict):
    is_sufficient: bool # Flag indicating if gathered information is sufficient
    knowledge_gap: str # Description of any identified knowledge gap
    follow_up_queries: Annotated[list, operator.add] # List of new queries (file paths) to explore
    research_loop_count: int # Current iteration count
    number_of_ran_queries: int # Total queries executed so far

# Represents a single query (file path)
class Query(TypedDict):
    query: str # The file path
    rationale: str # Justification for this query (less relevant for file paths)

# State for query generation node
class QueryGenerationState(TypedDict):
    query_list: list[Query] # List of Query objects to be processed

# State for the file reading node (web_research)
class WebSearchState(TypedDict): # State for the (file reading) node
    search_query: str # The file path to read
    id: str # An identifier for this specific read operation
```

### Algorithms & Processes (Backend Agent Flow)
The core logic resides in the LangGraph agent (`backend/src/agent/graph.py`):
1.  **`generate_query` Node:** Receives user query (within `OverallState.messages`). Uses an LLM (Gemini) to generate a list of file paths (`Query[]`) relevant to the user's query. The number of initial paths is determined by `OverallState.initial_search_query_count` (from frontend "Effort" setting).
2.  **`continue_to_web_research` Edge:** Routes each generated file path from `QueryGenerationState.query_list` to an instance of the `web_research` node.
3.  **`web_research` Node:** Takes a file path (`WebSearchState.search_query`). Calls `read_project_file` to read its content. Stores the content and source metadata in `OverallState.web_research_result` and `OverallState.sources_gathered`.
4.  **`reflection` Node:** Aggregates all file contents read so far (from `OverallState.web_research_result`). Uses an LLM (Gemini) to:
    *   Determine if the gathered information `is_sufficient` to answer the user's query.
    *   Identify any `knowledge_gap`.
    *   Generate `follow_up_queries` (more file paths to read) if needed and if `research_loop_count` < `max_research_loops`.
5.  **`evaluate_research` Edge (Conditional):**
    *   If `ReflectionState.is_sufficient` is true OR `OverallState.research_loop_count` reaches `OverallState.max_research_loops`: Proceeds to `finalize_answer`.
    *   Else (and `ReflectionState.follow_up_queries` exist): Routes new `follow_up_queries` back to the `web_research` node (via `generate_query` node which acts as a dispatcher for these new queries).
6.  **`finalize_answer` Node:** Takes all gathered file contents (from `OverallState.web_research_result` and `OverallState.sources_gathered`) and the original user query. Uses an LLM (Gemini) to synthesize a final answer, incorporating information from the files and implicitly citing them (as the content comes from `sources_gathered` which contains file paths). The result is added to `OverallState.messages`.

### Dependencies
*   **Backend (Python):**
    *   `langgraph`: Core framework for building the agent.
    *   `fastapi`: Web framework for serving the backend.
    *   `uvicorn`: ASGI server for FastAPI.
    *   `langchain-google-genai`: For interacting with Google Gemini models.
    *   `python-dotenv`: For managing environment variables (like API keys).
    *   `google-generativeai`: Google GenAI client library (though direct use in `graph.py` is minimal as LLM interaction is primarily via LangChain components).
*   **Frontend (JavaScript/TypeScript):**
    *   `react`: UI library.
    *   `@langchain/langgraph-sdk`: For connecting to and streaming from the LangGraph backend.
    *   `vite`: Build tool for the frontend.
    *   `tailwindcss`: CSS framework.
    *   `lucide-react`: Icon library.
    *   `shadcn/ui` components (Button, Select, ScrollArea, Card, Textarea, etc.).
    *   `react-markdown`: To render AI responses.
*   **External Services/APIs:**
    *   Google Gemini API: Required for LLM functionalities (query generation, reflection, answer synthesis). An API key (`GEMINI_API_KEY`) must be configured.
    *   (Note: The original project used Google Search API via Gemini model for web research; this TINS adaptation modifies the `web_research` node to read local files instead.)
    *   LangSmith API (Optional): For tracing and debugging LangGraph agents, as mentioned in deployment notes in the original README.

## Input/Output
*   **User Input:**
    *   Primary input is a textual query from the user via the frontend `Textarea`.
    *   Secondary inputs are "Effort" (Low, Medium, High) and "Model" (e.g., "2.0 Flash", "2.5 Pro") selections from dropdowns, which configure agent behavior.
*   **Data Flow (Frontend to Backend):**
    *   On submission, the frontend's `thread.submit()` sends a JSON object to the backend. Based on `App.tsx handleSubmit` and `OverallState` structure:
      ```json
      {
        "messages": [ /* Array of Message objects, e.g., { "type": "human", "content": "User query", "id": "..." } */ ],
        "initial_search_query_count": Number, // (e.g., 1, 3, or 5)
        "max_research_loops": Number, // (e.g., 1, 3, or 10)
        "reasoning_model": "gemini_model_name_string" // (e.g., "gemini-2.0-flash-preview-04-17")
      }
      ```
*   **Data Flow (Backend to Frontend - Streaming):**
    *   The backend streams events and messages. Key event structures processed by frontend's `onUpdateEvent`:
        *   `event.generate_query`: `{ "query_list": ["filepath1.md", "src/filepath2.py"] }` (example file paths)
        *   `event.web_research`: `{ "sources_gathered": [{ "type": "file", "source": "filepath.txt", "content": "File content...", "id": 0, "error": false/true }] }`
        *   `event.reflection`: `{ "is_sufficient": Boolean, "follow_up_queries": ["another_file.json"] }`
        *   `event.finalize_answer`: Presence indicates completion; specific data not directly used by frontend for timeline text beyond a generic message.
    *   Chat messages are streamed as an array of `Message` objects (from `@langchain/langgraph-sdk`), updating `thread.messages`.
*   **Output to User:**
    *   The final synthesized answer from the agent is displayed as an AI message in the chat UI, rendered as Markdown.
    *   The `ActivityTimeline` provides a trace of the agent's internal steps (file paths investigated, reflection outcomes).
    *   Citations are implicitly the file paths from which information was drawn, as reflected in `sources_gathered` and the timeline.

## Error Handling
*   **Backend:**
    *   **API Key:** `GEMINI_API_KEY` absence: `ValueError` raised in `graph.py` on initialization, preventing agent graph build.
    *   **LLM Calls:** `ChatGoogleGenerativeAI` instances are configured with `max_retries=2`. Persistent failures would likely cause the LangGraph agent run for that thread to error out. The stream to client might terminate or send an error event (LangGraph SDK behavior).
    *   **File Reading (`read_project_file` within `web_research` node of `graph.py`):**
        *   Catches `FileNotFoundError` and general `Exception`.
        *   An error message string is created. This message is included in the `content` field of an item in the `sources_gathered` list (with an `error: True` flag) and also as an item in the `web_research_result` list.
        *   Handles `Invalid file path type` (if query is not a string) similarly by returning an error message in `sources_gathered` and `web_research_result`.
        *   These error messages become part of the "researched data" and can be surfaced in the final AI answer if the `finalize_answer` LLM is prompted to do so.
*   **Frontend:**
    *   The React frontend (`App.tsx`, `ChatMessagesView.tsx`) does not have explicit, distinct UI components (like modals or global banners) for displaying errors from backend operations.
    *   The `onFinish` callback in `useStream` in `App.tsx` logs the event to the console, which could include error information if the stream terminates due to an error, but this is not directly shown to the user in the UI.
    *   If the backend agent includes error messages (e.g., file not found) within the regular AI message content, it would be rendered in `ChatMessagesView` via `ReactMarkdown`.
    *   Frontend input validation: Submit button is disabled if the input `Textarea` is empty.

## Technical Constraints & Notes
*   Requires Node.js (version for Vite/React, e.g., Node 20) for frontend and Python 3.11 for backend.
*   `GEMINI_API_KEY` environment variable must be set for the backend to function.
*   The number of LLM calls depends on the user's "Effort" setting (initial queries + reflection loops + final answer).
*   The `web_research` node has been specifically modified for this TINS adaptation to read local project files instead of performing live web searches. "Search queries" generated by the agent are treated as file paths relative to a predefined project root (not explicitly defined in draft, but implied for local file reading).
*   Production deployment, as suggested by the original project's README, would typically involve Redis (for pub-sub streaming) and Postgres (for persistence), but these are not part of the core logic analyzed for this TINS document and are not required for local execution as described.
*   The `backend/src/agent/app.py` serves the FastAPI application and includes logic to serve the static frontend build if found, otherwise returning a 503 error.
*   Docker build process (`Dockerfile`): Multi-stage, builds frontend with `node:20-alpine`, then backend with `docker.io/langchain/langgraph-api:3.11` using `uv` for Python dependencies.

## Acceptance Criteria (for an LLM generating this project from TINS)
An LLM successfully implementing this TINS specification should produce an application where:
1.  A user can submit a textual query via a web interface (React frontend).
2.  The backend agent (LangGraph/Python) interprets the query and generates a list of relevant project file paths to investigate using an LLM (Gemini).
3.  The agent reads content from these specified project files from the local filesystem.
4.  The agent reflects on the gathered content using an LLM, potentially deciding to read more files if needed, up to a configurable limit based on user's "Effort" setting.
5.  A final answer, synthesized by an LLM from the content of the read files, is displayed to the user in the web interface.
6.  The UI displays a timeline or log of the agent's main processing steps (e.g., query generation, file reading with paths, reflection outcomes).
7.  The user can control the "Effort" (number of initial files to check / depth of research loops) and the "Model" (underlying LLM for reasoning) via UI dropdowns.
8.  Communication between frontend and backend utilizes streaming for real-time updates of agent activity and chat messages.
9.  Basic error handling for missing files is present (e.g., agent reports inability to access a specified file, potentially in its final answer or timeline).
10. The application is containerizable using the provided `Dockerfile` structure.

## Visual Aids
*   **Application UI Screenshot:** `app.png` (located in the project root of the original repository)
*   **Backend Agent Flow Diagram:** `agent.png` (located in the project root of the original repository)

These diagrams (from the original project) provide visual context for the UI layout and backend agent logic.
