import os
import argparse
import sys
import re

from .tools_and_schemas import SearchQueryList, Reflection # Query potentially if direct override is used
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from .state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from .configuration import Configuration
from .prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
    read_project_file, # Added import for read_project_file from utils
)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph node that generates a search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search query for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated query
    """
    configurable = Configuration.from_runnable_config(config)

    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # init Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    research_topic_str = get_research_topic(state["messages"])
    # Regex to find potential file paths (e.g., quoted, or with extensions)
    # This is a simplified regex for demonstration
    file_path_match = re.search(r"['\"]?(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+\.[a-zA-Z0-9]+['\"]?", research_topic_str)

    if file_path_match:
        extracted_path = file_path_match.group(0).strip("'\"")
        # Refine the prompt to focus the LLM on this path
        formatted_prompt = (
            f"The user is asking about the file: '{extracted_path}'. "
            f"Your primary task is to confirm this file path. If it seems valid, output it directly. "
            f"If the query also asks a question about its content, that will be handled later. "
            f"Only output a single query containing this exact file path: {extracted_path}."
            f"\nOriginal research topic: {research_topic_str}"
            f"\nNumber of queries to generate: 1" # Force 1
        )
        # Update state to reflect we are focusing on 1 query
        state["initial_search_query_count"] = 1
    else:
        # Original prompt formatting if no specific path is found
        formatted_prompt = query_writer_instructions.format(
            current_date=current_date,
            research_topic=research_topic_str, # Use the extracted string
            number_queries=state["initial_search_query_count"],
        )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"query_list": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["query_list"])
    ]


# Local read_project_file and list_files_in_directory are removed.
# web_research will use read_project_file from .utils


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph node that reads a project file.

    Interprets the search_query as a file path and reads the content of the file.

    Args:
        state: Current graph state containing the search query (file path) and node id.
        config: Configuration for the runnable.

    Returns:
        Dictionary with state update, including sources_gathered and web_research_results.
    """
    file_path = state["search_query"]
    node_id = state["id"]

    # Basic check if it's a path (can be refined)
    # os.path.exists check is implicitly handled by read_project_file
    if not isinstance(file_path, str):
        # Handle non-string file path if necessary
        # For now, assume valid path or read_project_file handles it.
        error_message = f"Invalid file path type: {type(file_path)}. Expected a string."
        return {
            "sources_gathered": [{"type": "file", "source": "N/A", "content": error_message, "id": node_id, "error": True}],
            "search_query": [state["search_query"]],
            "web_research_result": [error_message],
        }

    # Call the imported read_project_file from utils.py
    file_data = read_project_file(file_path, node_id) # This now calls utils.read_project_file

    return {
        "sources_gathered": file_data["sources_gathered"],
        "search_query": [state["search_query"]], # Keep original query for consistency
        "web_research_result": file_data["web_research_result"],
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

    Analyzes the current summary to identify areas for further research and generates
    potential follow-up queries. Uses structured output to extract
    the follow-up query in JSON format.

    Args:
        state: Current graph state containing the running summary and research topic
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated follow-up query
    """
    configurable = Configuration.from_runnable_config(config)
    # Increment the research loop count and get the reasoning model
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    # init Reasoning Model
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

    # Format the prompt
    formatted_prompt = answer_instructions.format(
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # init Reasoning Model, default to Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": state["sources_gathered"], # Pass through the file sources
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pro Search Agent CLI")
    parser.add_argument(
        "--test-file-access",
        action="store",
        nargs="?",
        default=None,
        const=".",  # Default directory if flag is present without a value
        help="Test file access by listing files and reading the first file. Optionally provide a directory path.",
    )
    cli_args = parser.parse_args()

    if cli_args.test_file_access is not None:
        directory_path = cli_args.test_file_access
        print(f"Files in directory '{directory_path}':")

        # files = list_files_in_directory(directory_path) # This function is removed from graph.py
        # For the test CLI part, if it was important, it would need to import list_files_in_directory from utils too.
        # Or this test logic could be removed/simplified if not critical for agent execution.
        # For now, let's assume this test part of the CLI is not essential for the agent's core logic.
        # If list_files_in_directory is needed, it should be imported from .utils
        from .utils import list_files_in_directory as list_files_in_directory_util # Import it if needed for CLI test
        files = list_files_in_directory_util(directory_path)

        for f_name in files:
            print(f"- {f_name}")

        if files:
            first_file_path = os.path.join(directory_path, files[0])
            print(f"\nReading content of the first file: '{first_file_path}'")

            # The local read_project_file is removed.
            # If this test CLI needs to read a file, it should also use the util version.
            # However, read_project_file from utils expects node_id, which might not make sense here.
            # This test code might need more significant refactoring if it's to be kept.
            # For this subtask, the focus is on the agent nodes.
            # A simple way to test read_project_file from utils here:
            if os.path.exists(first_file_path):
                with open(first_file_path, "r") as f_content:
                    print("\nContent (direct read for test):")
                    print(f_content.read()[:500] + "...") # Print first 500 chars
            else:
                print(f"File {first_file_path} not found for direct read test.")

        else:
            print("No files found in the directory.")

        sys.exit(0)  # Exit after performing the test file access
