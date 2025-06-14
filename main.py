import sys
import httpx
import json
import uuid
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QComboBox,
    QPushButton,
    QListWidget,
    QSplitter,
    QTextBrowser,
    QLabel,
    QStatusBar,
    QMenuBar,
    QToolBar
)

DEBUG=True

# --- Backend Communication Thread ---
class BackendThread(QThread):
    new_message_signal = Signal(str, str)  # sender_type ("human", "ai"), content
    new_activity_signal = Signal(str)      # activity_text
    processing_error_signal = Signal(str)  # error_message
    processing_finished_signal = Signal()  # no args

    def __init__(self, query: str, effort_params: dict, model_name: str, thread_id: str):
        super().__init__()
        self.query = query
        self.effort_params = effort_params # e.g., {"initial_search_query_count": 1, "max_research_loops": 1}
        self.model_name = model_name
        self.thread_id = thread_id
        self._is_running = True

    def run(self):
        try:
            # Backend URL and endpoint (adjust if different)
            # Common LangGraph Python SDK endpoints are /invoke or /stream for a runnable
            backend_url = "http://localhost:8000/agent/invoke"
            # Or potentially /stream if the backend is set up for that specifically
            # For LangServe, the input is often just the input to the graph, and config is separate

            # Construct payload based on TINS Edition/README.md and typical LangGraph input
            # The exact structure for input messages might vary (e.g. just `{"input": "user query"}` or `{"input": {"question": "user query"}}`)
            # For a chat-like interaction, it's often `{"messages": [{"role": "user", "content": "query"}]}`
            # We'll use a structure that includes messages and config for thread_id
            payload = {
                "input": {
                    "messages": [{"type": "human", "content": self.query, "id": str(uuid.uuid4())[:8]}],
                    "initial_search_query_count": self.effort_params["initial_search_query_count"],
                    "max_research_loops": self.effort_params["max_research_loops"],
                    "reasoning_model": self.model_name, # Ensure this matches backend expectation
                },
                "config": {
                    "configurable": {"thread_id": self.thread_id}
                }
            }

            self.new_activity_signal.emit(f"Connecting to backend at {backend_url} with thread_id: {self.thread_id}")
            self.new_activity_signal.emit(f"Payload: {json.dumps(payload, indent=2)}")


            # Using httpx for streaming request
            # LangServe typically streams JSON objects separated by newlines, or SSEs.
            # For SSEs, you'd look for `event:` and `data:` lines.
            # For newline-delimited JSON, you read line by line.
            with httpx.stream("POST", backend_url, json=payload, timeout=None) as response:
                if response.status_code != 200:
                    error_content = response.read().decode()
                    self.processing_error_signal.emit(f"Backend error {response.status_code}: {error_content}")
                    return

                self.new_activity_signal.emit("Connected. Receiving stream...")
                for line in response.iter_lines():
                    if not self._is_running:
                        self.new_activity_signal.emit("Stream processing interrupted by client.")
                        break
                    if line:
                        try:
                            # Assuming newline-delimited JSON objects from LangServe stream
                            # Each `line` could be a JSON string representing an event
                            # e.g. {"event": "on_chat_model_stream", "data": {"chunk": {"content": "..."}}}
                            # or {"event": "on_tool_start", "data": {"name": "tool_name", "input": ...}}
                            # or custom events from your graph.

                            # A common pattern is that the entire stream is a sequence of JSON objects,
                            # each representing an event from the graph execution.
                            # We need to inspect these objects to decide what to show.

                            event_data = json.loads(line)
                            event_type = event_data.get("event")
                            data_content = event_data.get("data", {})
                            run_name = event_data.get("name", "") # Name of the node/step

                            # Log generic event for activity timeline
                            activity_log_entry = f"Event: {event_type}, Node: {run_name}"
                            if data_content:
                                # Add some data to the log, but keep it concise
                                if "chunk" in data_content and isinstance(data_content["chunk"], dict) and "content" in data_content["chunk"]:
                                     activity_log_entry += f", Chunk: {str(data_content['chunk']['content'])[:30]}..."
                                elif "input" in data_content:
                                     activity_log_entry += f", Input: {str(data_content['input'])[:30]}..."

                            self.new_activity_signal.emit(activity_log_entry)

                            # Example: Extracting AI messages (modify based on actual stream structure)
                            # This depends heavily on how your LangGraph agent streams final answers or intermediate messages.
                            # If it's a chat model stream:
                            if event_type == "on_chat_model_stream":
                                if isinstance(data_content.get("chunk"), dict) and "content" in data_content["chunk"]:
                                    ai_message_part = data_content["chunk"]["content"]
                                    if ai_message_part: # Ensure it's not an empty string
                                        # Emit as an AI message. The main thread might need to accumulate these.
                                        # For now, let's send each part.
                                        self.new_message_signal.emit("ai_partial", ai_message_part)

                            # If the event indicates a final answer from a specific node:
                            # This is highly dependent on your graph's structure.
                            # Let's assume a node named "FinalAnswerNode" (you'd replace this)
                            # produces the final, complete AI message in its output.
                            # Or, if the last event from "on_chat_model_stream" implies the end of a message.
                            # LangGraph might also have an "on_chain_end" or similar for the whole graph.
                            # For now, we'll rely on `processing_finished_signal` upon stream end.
                            # And the main window will piece together partial messages if needed.

                            # Add more specific parsing based on expected events from your LangGraph agent
                            # e.g., if specific nodes log particular types of activities.
                            # For instance, if a tool call is made:
                            if event_type == "on_tool_start":
                                tool_name = data_content.get("name", "Unknown Tool")
                                tool_input = str(data_content.get("input", {}))
                                self.new_activity_signal.emit(f"Tool Started: {tool_name} with input: {tool_input[:50]}...")
                            elif event_type == "on_tool_end":
                                tool_name = data_content.get("name", "Unknown Tool")
                                tool_output = str(data_content.get("output", ""))
                                self.new_activity_signal.emit(f"Tool Ended: {tool_name}, Output: {tool_output[:50]}...")


                        except json.JSONDecodeError:
                            self.new_activity_signal.emit(f"Received non-JSON line: {line[:100]}") # Log it but don't crash
                        except Exception as e:
                            self.new_activity_signal.emit(f"Error processing stream line: {e}")


        except httpx.RequestError as e:
            self.processing_error_signal.emit(f"Network request failed: {e}")
        except Exception as e:
            self.processing_error_signal.emit(f"An unexpected error occurred in backend thread: {e}")
        finally:
            self.new_activity_signal.emit("Stream finished or connection closed.")
            self.processing_finished_signal.emit()

    def stop(self):
        self._is_running = False
        self.new_activity_signal.emit("Attempting to stop backend thread...")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend_thread = None
        self.current_ai_message = "" # To accumulate partial AI messages
        self.setWindowTitle("TINS Agent PySide6 GUI")
        self.setGeometry(100, 100, 1200, 800)

        # self.is_processing = False # Replaced by checking self.backend_thread

        # --- Menu Bar ---
        self.menu_bar = QMenuBar() # Corrected: was self.menuBar()
        self.file_menu = self.menu_bar.addMenu("&File")
        self.new_search_action = self.file_menu.addAction("&New Search") # Corrected: was self.file_menu.addAction()
        self.new_search_action.triggered.connect(self.handle_new_search)
        self.exit_action = self.file_menu.addAction("&Exit") # Corrected: was self.file_menu.addAction()
        self.exit_action.triggered.connect(self.close) # Corrected: was self.close
        self.setMenuBar(self.menu_bar) # Corrected: was self.setMenuBar()

        # --- Main Widget and Layout ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Top Splitter (Chat & Activity Timeline) ---
        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Chat Display Area
        self.chat_display_area = QTextBrowser()
        self.chat_display_area.setPlaceholderText("Conversation history will appear here...")
        self.top_splitter.addWidget(self.chat_display_area)

        # Activity Timeline
        self.activity_timeline = QListWidget()
        self.top_splitter.addWidget(self.activity_timeline)

        self.top_splitter.setSizes([700, 300])

        # --- Bottom Pane (Input & Controls) ---
        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_widget)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your research query here...")
        self.query_input.setFixedHeight(100)
        self.bottom_layout.addWidget(self.query_input)

        self.controls_layout = QHBoxLayout()
        self.effort_label = QLabel("Effort:")
        self.controls_layout.addWidget(self.effort_label)
        self.effort_combo = QComboBox()
        self.effort_combo.addItems(["Low", "Medium", "High"])
        self.controls_layout.addWidget(self.effort_combo)

        self.model_label = QLabel("Model:")
        self.controls_layout.addWidget(self.model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Gemini 1.5 Flash", "Gemini 1.5 Pro", "Claude 3 Sonnet", "GPT-4o"])
        self.controls_layout.addWidget(self.model_combo)
        self.controls_layout.addStretch()

        self.search_stop_button = QPushButton("Search")
        self.search_stop_button.clicked.connect(self.handle_search_stop)
        self.controls_layout.addWidget(self.search_stop_button)

        self.new_search_button = QPushButton("New Search")
        self.new_search_button.clicked.connect(self.handle_new_search)
        self.controls_layout.addWidget(self.new_search_button)

        self.copy_ai_message_button = QPushButton("Copy Last AI Message")
        self.copy_ai_message_button.clicked.connect(self.handle_copy_ai_message)
        self.controls_layout.addWidget(self.copy_ai_message_button)

        self.bottom_layout.addLayout(self.controls_layout)
        self.bottom_widget.setFixedHeight(180)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(self.bottom_widget)
        self.main_splitter.setSizes([600, 200])
        self.main_layout.addWidget(self.main_splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready.")
        if DEBUG: print(f"Ready.")

        self.handle_new_search()

    def _get_effort_params(self):
        effort_text = self.effort_combo.currentText()
        if effort_text == "Low":
            return {"initial_search_query_count": 1, "max_research_loops": 1}
        elif effort_text == "Medium":
            return {"initial_search_query_count": 3, "max_research_loops": 3}
        elif effort_text == "High":
            return {"initial_search_query_count": 5, "max_research_loops": 5} # As per TINS Edition/README.md (5/10 example, using 5/5 for now)
        return {"initial_search_query_count": 1, "max_research_loops": 1} # Default


    @Slot()
    def handle_search_stop(self):
        if self.backend_thread and self.backend_thread.isRunning():
            # Stop Search
            self.backend_thread.stop() # Signal the thread to stop
            # self.backend_thread.quit() # Request event loop to exit
            # self.backend_thread.wait(5000) # Wait for thread to finish, with timeout
            # If still running after wait, terminate (use with caution)
            # if self.backend_thread.isRunning():
            #     self.backend_thread.terminate()
            #     self.activity_timeline.addItem("Backend thread forcefully terminated.")

            self.search_stop_button.setText("Search")
            self.query_input.setEnabled(True)
            self.effort_combo.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.new_search_button.setEnabled(True)
            self.new_search_action.setEnabled(True)
            self.status_bar.showMessage("Processing stopped by user.", 5000)
            if DEBUG: print(f"Processing stopped by user.", 5000)
            self.activity_timeline.addItem("Processing stopped by user.")
            self.backend_thread = None # Allow it to be garbage collected after it finishes
        else:
            # Start Search
            query_text = self.query_input.toPlainText().strip()
            if not query_text:
                self.status_bar.showMessage("Error: Query cannot be empty.", 5000)
                if DEBUG: print(f"Error: Query cannot be empty.", 5000)
                return

            selected_effort_params = self._get_effort_params()
            selected_model = self.model_combo.currentText()

            # Append user message to chat display immediately
            self._update_chat_display("human", query_text)
            self.query_input.clear()
            self.current_ai_message = "" # Reset any accumulated AI message

            self.search_stop_button.setText("Stop")
            self.query_input.setEnabled(False)
            self.effort_combo.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.new_search_button.setEnabled(False)
            self.new_search_action.setEnabled(False)
            self.status_bar.showMessage("Processing query...")
            if DEBUG: print(f"Processing query...")

            self.activity_timeline.addItem(f"Query submitted (Effort: {self.effort_combo.currentText()}, Model: {selected_model})")

            # Generate a new thread_id for this search session
            thread_id = str(uuid.uuid4())

            self.backend_thread = BackendThread(query_text, selected_effort_params, selected_model, thread_id)
            self.backend_thread.new_message_signal.connect(self._update_chat_display)
            self.backend_thread.new_activity_signal.connect(self._update_activity_log)
            self.backend_thread.processing_error_signal.connect(self._handle_processing_error)
            self.backend_thread.processing_finished_signal.connect(self._handle_processing_finished)
            self.backend_thread.finished.connect(self._on_thread_actually_finished) # For cleanup

            self.backend_thread.start()

    @Slot(str, str)
    def _update_chat_display(self, sender_type, content):
        if sender_type == "human":
            self.chat_display_area.append(f"<b>You:</b> {content}<br>")
        elif sender_type == "ai_partial":
            self.current_ai_message += content
            # Update the last AI message in place. This is tricky with QTextBrowser's append.
            # A more robust way is to remove the last line if it's an AI message and re-append.
            # For simplicity here, we might append, or if it's the very start of an AI message:
            if not self.chat_display_area.toPlainText().endswith("</b><br>"): # if last message was not user
                 # Attempt to update the current AI message block.
                 # This is a simplification. A proper way would be to track message boundaries.
                 current_html = self.chat_display_area.toHtml()
                 # Find last opening <b>AI...</b> tag and replace content up to <br>
                 # This is too complex for simple replacement, let's just append partials for now
                 # and finalize when the full message is assumed complete or stream ends.
                 # self.chat_display_area.append(f"<i>AI partial:</i> {content}") # Temporary
                 # Or, let's assume for now that the backend sends full messages or we handle accumulation better
                 self.chat_display_area.append(f"{content}") # This will make stream look like separate messages

            else: # Start of a new AI message block
                 self.chat_display_area.append(f"<b>AI ({self.model_combo.currentText()}):</b> {content}")
        elif sender_type == "ai_final": # A signal for a complete AI message
            self.chat_display_area.append(f"<b>AI ({self.model_combo.currentText()}):</b> {content}<br>")
            self.current_ai_message = "" # Reset for next message
        self.chat_display_area.ensureCursorVisible()


    @Slot(str)
    def _update_activity_log(self, activity_text):
        self.activity_timeline.addItem(activity_text)
        self.activity_timeline.scrollToBottom()

    @Slot(str)
    def _handle_processing_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}", 10000)
        if DEBUG: print(f"Error: {error_message}", 10000)
        self.activity_timeline.addItem(f"ERROR: {error_message}")
        self._reset_ui_after_processing()

    @Slot()
    def _handle_processing_finished(self):
        self.status_bar.showMessage("Processing finished.", 5000)
        if DEBUG: print(f"Processing finished.", 5000)
        if self.current_ai_message: # If there's an unfinished AI message part
            # This logic might need refinement based on how backend signals end of message
            # self._update_chat_display("ai_final", self.current_ai_message)
            # For now, assume any remaining partial message is the end.
             self.chat_display_area.append("<br>") # Add a line break if it was streaming.
        self.current_ai_message = ""
        self._reset_ui_after_processing()

    @Slot()
    def _on_thread_actually_finished(self):
        # This slot is connected to QThread.finished signal
        # It's a good place for any final cleanup of the thread object itself
        if self.backend_thread: # Check if it wasn't already set to None by stop action
            self.activity_timeline.addItem(f"Backend thread ({self.backend_thread.objectName() if self.backend_thread.objectName() else 'ID: '+str(self.backend_thread.currentThread())}) has finished execution.")
        self.backend_thread = None # Ensure it's cleared

    def _reset_ui_after_processing(self):
        self.search_stop_button.setText("Search")
        self.query_input.setEnabled(True)
        self.effort_combo.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.new_search_button.setEnabled(True)
        self.new_search_action.setEnabled(True)
        # if self.backend_thread:
        #     self.backend_thread = None # Clear the thread reference


    @Slot()
    def handle_new_search(self):
        if self.backend_thread and self.backend_thread.isRunning():
            self.backend_thread.stop()
            # Consider waiting briefly or ensuring thread is cleaned up.
            # For now, we'll just signal it and reset UI.
            self._reset_ui_after_processing() # Reset UI elements

        self.query_input.clear()
        self.chat_display_area.clear()
        self.activity_timeline.clear()
        self.current_ai_message = ""

        self.effort_combo.setCurrentIndex(0)
        self.model_combo.setCurrentIndex(0)

        self._reset_ui_after_processing() # Ensures button text and enabled states are correct

        self.activity_timeline.addItem("New search session started. Enter your query.")
        self.status_bar.showMessage("Ready for new search.", 5000)
        if DEBUG: print(f"Ready for new search.", 5000)

    @Slot()
    def handle_copy_ai_message(self):
        selected_text = self.chat_display_area.textCursor().selectedText()
        if selected_text:
            QApplication.clipboard().setText(selected_text)
            self.status_bar.showMessage("Selected text copied to clipboard.", 3000)
            if DEBUG: print(f"Selected text copied to clipboard.", 3000)
        else:
            # Attempt to find the last AI message block.
            # This is a heuristic and might not be perfectly robust.
            html_content = self.chat_display_area.toHtml()
            # Split by what we assume AI messages start with (could be more specific)
            # This is a very naive way to get the "last AI message"
            parts = html_content.split(f"<b>AI ({self.model_combo.currentText()}):</b>")
            if len(parts) > 1:
                last_ai_html = parts[-1].split("<br>")[0] # Get content before the next line break
                # Convert HTML to plain text for clipboard
                temp_browser = QTextBrowser()
                temp_browser.setHtml(last_ai_html)
                plain_text = temp_browser.toPlainText()
                QApplication.clipboard().setText(plain_text.strip())
                self.status_bar.showMessage("Last AI message copied to clipboard.", 3000)
                if DEBUG: print(f"Last AI message copied to clipboard.", 3000)
            elif self.chat_display_area.toPlainText().strip():
                 QApplication.clipboard().setText(self.chat_display_area.toPlainText())
                 self.status_bar.showMessage("Chat content copied (could not identify specific AI message).", 3000)
                 if DEBUG: print(f"Chat content copied (could not identify specific AI message).", 3000)
            else:
                 self.status_bar.showMessage("Chat display is empty.", 3000)
                 if DEBUG: print(f"Chat display is empty.", 3000)

    def closeEvent(self, event):
        if self.backend_thread and self.backend_thread.isRunning():
            self.backend_thread.stop()
            # self.backend_thread.quit()
            # self.backend_thread.wait(1000) # Give it a moment to close
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
