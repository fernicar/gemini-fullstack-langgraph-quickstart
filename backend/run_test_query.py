import os
import uuid
from pathlib import Path

# Load environment variables (especially GEMINI_API_KEY)
# This should be one of the first things to do.
from dotenv import load_dotenv
# Assuming run_test_query.py is in /app/backend/
# .env should be in /app/
project_root_for_env = Path(__file__).resolve().parents[1]
dotenv_path = project_root_for_env / ".env"
load_dotenv(dotenv_path)

# Ensure PYTHONPATH is set up correctly if running from a different root
# For example, if running `python backend/run_test_query.py` from project root,
# Python should be able to find `backend.src`
try:
    from backend.src.agent.graph import graph # Assuming 'graph' is the compiled agent
except ModuleNotFoundError:
    # Attempt to adjust PYTHONPATH if running script directly from backend directory
    import sys
    # project_root is already defined as project_root_for_env
    if str(project_root_for_env) not in sys.path:
        sys.path.insert(0, str(project_root_for_env))
    from backend.src.agent.graph import graph

from langchain_core.messages import HumanMessage


def run_test():
    if os.getenv("GEMINI_API_KEY") is None:
        print("GEMINI_API_KEY is not set. Please set it in your .env file or environment.")
        return

    test_query = "what's the protagonist's iconic phrase?"
    # The agent's read_project_file utility seems to expect paths relative to project root
    # or be able to handle absolute paths if the `generate_query` node produces them.
    # The current `read_project_file` in graph.py uses `open(file_path, "r")`
    # which will be relative to CWD if file_path is relative.
    # The `generate_query` node in the graph.py is LLM based, so we give it a strong hint.
    # The `web_research` node takes the output of `generate_query` as the file_path.

    # Path relative to the project root for clarity and consistency with how tools might work
    target_file_relative_to_project_root = "backend/test_data/protagonist_info.txt"

    # Check if the file exists to provide a better error message if not
    target_file_absolute_path = Path(__file__).resolve().parents[1] / target_file_relative_to_project_root
    if not target_file_absolute_path.exists():
        print(f"ERROR: Test data file not found at {target_file_absolute_path}")
        print("Please ensure the file exists and the path is correct.")
        return

    thread_id = str(uuid.uuid4())

    # To ensure the agent focuses on the file, we make the file path the primary subject.
    # The agent's `generate_query` node is responsible for creating file paths.
    # We are essentially telling it "this is the file path I want you to use".
    # The `web_research` node will then use this path.
    # initial_search_query_count = 1 should make it focus on this single "query" (which is the file path)
    input_payload = {
        "messages": [HumanMessage(content=f"What is the protagonist's iconic phrase? Search for this information in the project file named '{target_file_relative_to_project_root}'.")],
        "initial_search_query_count": 1,
        "max_research_loops": 0, # Set to 0 to prevent reflection and further searches after the initial query generation.
        "reasoning_model": "gemini-1.5-flash-latest", # Ensure this model is available
    }
    config = {"configurable": {"thread_id": thread_id}}

    print(f"Invoking agent with thread_id: {thread_id}")
    print(f"Target file: {target_file_relative_to_project_root}")
    print(f"Query: {test_query}")
    print("Please wait for the agent to process...")

    try:
        # The agent's `generate_query` node creates search queries.
        # If `initial_search_query_count` is 1 and the prompt is specific,
        # it should generate the target file path as the "search query".
        # The `web_research` node then uses this "search query" as a file path.
        final_state = graph.invoke(input_payload, config=config)

        ai_response = ""
        # The final answer is usually in the 'messages' list of the final state, from the AI.
        if final_state and "messages" in final_state and isinstance(final_state["messages"], list):
            for msg in reversed(final_state["messages"]):
                if hasattr(msg, 'type') and (msg.type == "ai" or msg.type == "assistant"): # Langchain AIMessage
                    ai_response = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("type") == "ai": # If messages are dicts
                    ai_response = msg.get("content")
                    break

        print("\n--- Agent Invocation Complete ---")
        if ai_response:
            print(f"AI Response: {ai_response}")
        else:
            print("No AI response found in the final state.")
            print("Final state details:")
            # Print relevant parts of the final state for debugging
            if final_state and "messages" in final_state:
                print(f"  Messages: {final_state['messages']}")
            if final_state and "web_research_result" in final_state:
                 print(f"  Web Research Result: {final_state['web_research_result']}")
            if final_state and "sources_gathered" in final_state:
                 print(f"  Sources Gathered: {final_state['sources_gathered']}")


    except Exception as e:
        print(f"An error occurred during agent invocation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
