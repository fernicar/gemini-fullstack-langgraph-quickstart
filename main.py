import sys
import httpx
import json
import uuid
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal
from pathlib import Path # For Path.home() in handle_browse_folder
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLineEdit,     # Added QLineEdit
    QFileDialog,   # Added QFileDialog
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

# --- Model API Name Mapping ---
# Ensure keys match the display names in model_combo in MainWindow
MODEL_API_MAP = {
    "Gemini 1.5 Flash": "gemini-1.5-flash-latest", # Google's API often uses this format
    "Gemini 1.5 Pro": "gemini-1.5-pro-latest",
    # For other models, we pass their names as-is.
    # The backend will error if it doesn't support them, but it won't be a Google "model name format" error.
    "Claude 3 Sonnet": "claude-3-sonnet-20240229",
    "GPT-4o": "gpt-4o",
}

# --- Debug Flag for Streaming ---
DEBUG_STREAM = True # Or False, or load from environment variable


# --- Backend Communication Thread ---
class BackendThread(QThread):
    new_message_signal = Signal(str, str)  # sender_type ("human", "ai_partial", "ai_final"), content
    new_activity_signal = Signal(str)      # activity_text
    processing_error_signal = Signal(str)  # error_message
    processing_finished_signal = Signal()  # no args

    def __init__(self, query: str, effort_params: dict, model_name: str, thread_id: str, target_folder: str = None): # Added target_folder
        super().__init__()
        self.query = query
        self.effort_params = effort_params
        self.model_name = model_name
        self.thread_id = thread_id
        self.target_folder = target_folder # Store target_folder
        self._is_running = True

    def run(self):
        try:
            backend_url = "http://localhost:8000/agent/invoke"

            selected_model_display_name = self.model_name
            # Use a default if not found (i.e., pass the original name)
            api_model_name = MODEL_API_MAP.get(selected_model_display_name, selected_model_display_name)

            payload = {
                "input": {
                    "messages": [{"type": "human", "content": self.query, "id": str(uuid.uuid4())[:8]}],
                    "initial_search_query_count": self.effort_params["initial_search_query_count"],
                    "max_research_loops": self.effort_params["max_research_loops"],
                    "reasoning_model": api_model_name,
                    "search_query": [],
                    "web_research_result": [],
                    "sources_gathered": [],
                    "research_loop_count": 0,
                    "target_folder": self.target_folder if self.target_folder else "", # Add target_folder to payload
                },
                "config": {
                    "configurable": {"thread_id": self.thread_id}
                }
            }

            self.new_activity_signal.emit(f"Connecting to backend at {backend_url} with thread_id: {self.thread_id}")
            # self.new_activity_signal.emit(f"Payload: {json.dumps(payload, indent=2)}") # Maybe too verbose for default log

            with httpx.stream("POST", backend_url, json=payload, timeout=None) as response:
                if response.status_code != 200:
                    error_content = response.read().decode()
                    self.processing_error_signal.emit(f"Backend error {response.status_code}: {error_content}")
                    return

                self.new_activity_signal.emit("Connected. Receiving stream...")
                for line in response.iter_lines():
                    if DEBUG_STREAM:
                        print(f"[RAW_STREAM_DATA] {line}")

                    if not self._is_running:
                        self.new_activity_signal.emit("Stream processing interrupted by client.")
                        break

                    if line:
                        try:
                            event_data = json.loads(line)
                            activity_to_log = ""
                            message_found_in_line = False

                            # Check for standard LangServe events first
                            event_type = event_data.get("event")
                            data_payload = event_data.get("data", {}) # 'data' is common
                            run_name = event_data.get("name", "")    # 'name' for node

                            if event_type:
                                message_found_in_line = True # Assume event line is handled
                                activity_to_log = f"Event: {event_type}, Node: {run_name}"
                                chunk_content = data_payload.get("chunk", {}).get("content") if isinstance(data_payload.get("chunk"), dict) else None

                                if event_type == "on_chat_model_stream" and chunk_content:
                                    self.new_message_signal.emit("ai_partial", chunk_content)
                                    activity_to_log += f", AI_Chunk: {str(chunk_content)[:30]}..."
                                elif event_type == "on_tool_start":
                                    tool_name = data_payload.get("name", "Unknown Tool")
                                    tool_input = str(data_payload.get("input", {}))
                                    activity_to_log += f", ToolStart: {tool_name}, Input: {tool_input[:30]}..."
                                elif event_type == "on_tool_end":
                                    tool_name = data_payload.get("name", "Unknown Tool")
                                    tool_output = str(data_payload.get("output", ""))
                                    activity_to_log += f", ToolEnd: {tool_name}, Output: {tool_output[:30]}..."
                                elif event_type == "on_chain_end":
                                    final_output_data = data_payload.get("output")
                                    if isinstance(final_output_data, dict) and "messages" in final_output_data:
                                        for msg in final_output_data["messages"]:
                                            if msg.get("type") == "ai" or msg.get("type") == "assistant":
                                                self.new_message_signal.emit("ai_final", msg.get("content", ""))
                                                activity_to_log += f", FinalAIMessage (on_chain_end): {str(msg.get('content',''))[:30]}..."
                                                break
                                    elif isinstance(final_output_data, str):
                                         self.new_message_signal.emit("ai_final", final_output_data)
                                         activity_to_log += f", FinalOutputStr (on_chain_end): {final_output_data[:30]}..."
                                # Add other specific event type handling if needed

                            # If not a standard event, check for the final output structure like {"output": {"messages": [...]}}
                            elif "output" in event_data and isinstance(event_data["output"], dict):
                                output_content = event_data["output"]
                                if "messages" in output_content and isinstance(output_content["messages"], list):
                                    message_found_in_line = True
                                    for msg_idx, msg_data in enumerate(output_content["messages"]):
                                        if isinstance(msg_data, dict) and (msg_data.get("type") == "ai" or msg_data.get("type") == "assistant"):
                                            ai_content = msg_data.get("content", "")
                                            self.new_message_signal.emit("ai_final", ai_content)
                                            activity_to_log = f"FinalAIMessage (from output.messages): {ai_content[:30]}..."
                                            break
                                    if not activity_to_log:
                                        activity_to_log = f"OutputFieldParsed: Parsed output.messages but no AI message found."

                                elif not activity_to_log :
                                     activity_to_log = f"OutputFieldContent: {str(output_content)[:100]}"


                            # Fallback for other direct message structures
                            elif isinstance(event_data, dict) and "messages" in event_data:
                                 message_found_in_line = True
                                 messages = event_data["messages"]
                                 if isinstance(messages, list):
                                    for msg in messages:
                                        if isinstance(msg, dict) and (msg.get("type") == "ai" or msg.get("type") == "assistant"):
                                            self.new_message_signal.emit("ai_final", msg.get("content", ""))
                                            activity_to_log = f"DirectAIMessage (from root.messages): {str(msg.get('content',''))[:30]}..."
                                            break
                                 if not activity_to_log:
                                    activity_to_log = f"RootMessagesParsed: Parsed root.messages but no AI message found."


                            if not message_found_in_line or not activity_to_log:
                                activity_to_log = f"UnknownStreamObjectOrNoRelevantData: {str(event_data)[:100]}"

                            if activity_to_log:
                                self.new_activity_signal.emit(activity_to_log)

                        except json.JSONDecodeError:
                            self.new_activity_signal.emit(f"Received non-JSON line: {line[:100]}")
                        except Exception as e:
                            self.new_activity_signal.emit(f"Error processing stream line: {str(e)[:100]}")
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

        # Folder Path Input
        self.folder_path_label = QLabel("Research Folder:")
        self.controls_layout.addWidget(self.folder_path_label)

        self.folder_path_input = QLineEdit()
        self.folder_path_input.setPlaceholderText("Select a folder containing files for research...")
        self.folder_path_input.setMinimumWidth(250)
        self.controls_layout.addWidget(self.folder_path_input)

        self.browse_folder_button = QPushButton("Browse...")
        self.browse_folder_button.clicked.connect(self.handle_browse_folder)
        self.controls_layout.addWidget(self.browse_folder_button)

        self.controls_layout.addSpacing(20) # Add a little space before "Effort"

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

            self._reset_ui_after_processing() # Resets buttons and enables inputs
            self.status_bar.showMessage("Processing stopped by user.", 5000)
            self.activity_timeline.addItem("Processing stopped by user.")
            # self.backend_thread is set to None in _on_thread_actually_finished or _reset_ui_after_processing
            if self.backend_thread : # ensure it's not already None
                self.backend_thread = None
        else:
            # Start Search
            query_text = self.query_input.toPlainText().strip()
            target_folder = self.folder_path_input.text().strip() # Get the folder path

            if not query_text:
                self.status_bar.showMessage("Error: Query cannot be empty.", 5000)
                return

            # Optional: Validate target_folder or decide if it's mandatory
            if not target_folder:
                # self.status_bar.showMessage("Warning: No research folder selected. Agent will use its default behavior.", 5000)
                pass # Pass it as empty or None to backend thread


            selected_effort_params = self._get_effort_params()
            selected_model = self.model_combo.currentText()

            self._update_chat_display("human", query_text)
            self.query_input.clear()
            self.current_ai_message = ""

            self.search_stop_button.setText("Stop")
            self.query_input.setEnabled(False)
            self.folder_path_input.setEnabled(False) # Disable folder input during search
            self.browse_folder_button.setEnabled(False) # Disable browse button
            self.effort_combo.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.new_search_button.setEnabled(False)
            self.new_search_action.setEnabled(False)
            self.status_bar.showMessage("Processing query...")

            self._update_chat_display("human", query_text) # Moved after disabling inputs and setting message
            self.activity_timeline.addItem(f"Query submitted (Effort: {self.effort_combo.currentText()}, Model: {selected_model}, Folder: {target_folder if target_folder else 'N/A'})")

            thread_id = str(uuid.uuid4())

            self.backend_thread = BackendThread(
                query_text,
                selected_effort_params,
                selected_model,
                thread_id,
                target_folder # Pass the new folder path
            )
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
            self.current_ai_message = "" # Clear any pending AI message when user sends something
        elif sender_type == "ai_partial":
            if not self.current_ai_message: # First part of a new AI message
                self.chat_display_area.append(f"<b>AI ({self.model_combo.currentText()}):</b> ") # Start new block
            self.chat_display_area.insertPlainText(content) # Append text without newline
            self.current_ai_message += content
        elif sender_type == "ai_final":
            if not self.current_ai_message: # If final came as one shot
                self.chat_display_area.append(f"<b>AI ({self.model_combo.currentText()}):</b> {content}<br>")
            else: # Finalizing a partial stream
                # self.chat_display_area.insertPlainText(content) # This would append if content is just the final part
                # Assuming 'content' here is the FULL final message if different from accumulated
                # If 'content' is just the last chunk, then current_ai_message already has most of it.
                # For now, let's assume 'content' is the complete final message.
                # We need to remove the partially constructed message first. This is hard with QTextBrowser.
                # A simpler approach for now if content is the full message:
                # Clear current_ai_message if it was being built, and append the final one.
                # This might cause a slight flicker or redraw of the AI message.
                # A truly smooth stream would require more complex QTextCursor manipulation.

                # Simplification: If there was a partial stream, assume `content` is the last chunk.
                if self.current_ai_message and content != self.current_ai_message : # if content is truly just the last part
                    self.chat_display_area.insertPlainText(content)
                elif not self.current_ai_message : # if it's a one-shot final message
                     self.chat_display_area.append(f"<b>AI ({self.model_combo.currentText()}):</b> {content}")

                self.chat_display_area.append("<br>") # Add the line break
            self.current_ai_message = "" # Reset for next message
        self.chat_display_area.ensureCursorVisible()


    @Slot(str)
    def _update_activity_log(self, activity_text):
        self.activity_timeline.addItem(activity_text)
        self.activity_timeline.scrollToBottom()

    @Slot(str)
    def _handle_processing_error(self, error_message):
        self.status_bar.showMessage(f"Error: {error_message}", 10000)
        self.activity_timeline.addItem(f"ERROR: {error_message}")
        self._reset_ui_after_processing()

    @Slot()
    def _handle_processing_finished(self):
        self.status_bar.showMessage("Processing finished.", 5000)
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
        self.folder_path_input.setEnabled(True) # Re-enable folder input
        self.browse_folder_button.setEnabled(True) # Re-enable browse button
        self.effort_combo.setEnabled(True)
        self.model_combo.setEnabled(True)
        self.new_search_button.setEnabled(True)
        self.new_search_action.setEnabled(True)
        if self.backend_thread is None : # only set to None if not already handled by stop
             self.backend_thread = None


    @Slot()
    def handle_browse_folder(self):
        # Get the current path from the line edit, if any, to start the dialog there
        current_path = self.folder_path_input.text()
        if not current_path:
            # Default to home directory or current working directory if field is empty
            current_path = str(Path.home()) # Or os.getcwd()

        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Research Folder",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder_path: # If a folder was selected (dialog not cancelled)
            self.folder_path_input.setText(folder_path)
            self.status_bar.showMessage(f"Folder selected: {folder_path}", 3000)

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

    @Slot()
    def handle_copy_ai_message(self):
        selected_text = self.chat_display_area.textCursor().selectedText()
        if selected_text:
            QApplication.clipboard().setText(selected_text)
            self.status_bar.showMessage("Selected text copied to clipboard.", 3000)
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
            elif self.chat_display_area.toPlainText().strip():
                 QApplication.clipboard().setText(self.chat_display_area.toPlainText())
                 self.status_bar.showMessage("Chat content copied (could not identify specific AI message).", 3000)
            else:
                 self.status_bar.showMessage("Chat display is empty.", 3000)

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
