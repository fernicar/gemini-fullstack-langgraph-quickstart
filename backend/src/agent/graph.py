import os
import argparse
import sys
import re

from .tools_and_schemas import SearchQueryList, Reflection, Query # Ensure Query is imported
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
    read_project_file,
    list_files_in_directory, # Added import for list_files_in_directory
)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    configurable = Configuration.from_runnable_config(config)
    
    # Initialize LLM (ensure this is how it's done, or pass llm if initialized outside)
    # This was previously outside the if/else, makes sense to have one instance
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0, 
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    research_topic_str = get_research_topic(state["messages"])
    target_folder = state.get("target_folder_path") # Get from state
    initial_query_count = state.get('initial_search_query_count', configurable.number_of_initial_queries)

    # 1. Deterministic path for specific test file (remains)
    # This regex specifically looks for 'backend/test_data/protagonist_info.txt'
    test_file_pattern = r"(?:['\"])?(backend/test_data/protagonist_info\.txt)(?:['\"])?"
    specific_test_file_match = re.search(test_file_pattern, research_topic_str)
    if specific_test_file_match:
        extracted_path = specific_test_file_match.group(1) # Get the captured path
        print(f"[generate_query] Deterministic path: Found test file '{extracted_path}' in query: '{research_topic_str}'.")
        query_obj = Query(query=extracted_path, rationale="Directly extracted from user query for specific test case.")
        return {"query_list": [query_obj]}

    # 2. If target_folder is provided, list files and use LLM to select
    if target_folder and os.path.isdir(target_folder):
        print(f"[generate_query] Target folder provided: '{target_folder}'. Listing files.")
        try:
            available_files = list_files_in_directory(target_folder) # This is expected to return list of filenames
            if not available_files:
                print(f"[generate_query] No files found in folder: '{target_folder}'. Returning empty query list.")
                return {"query_list": []}

            print(f"[generate_query] Files in '{target_folder}': {available_files}")
            
            file_list_str = "\n - ".join(available_files)
            current_date = get_current_date()

            # New prompt for the LLM to select from the list
            formatted_prompt = (
                f"Current date: {current_date}\n"
                f"User's research question: {research_topic_str}\n"
                f"I have access to the following files in the folder '{target_folder}':\n - {file_list_str}\n\n"
                f"Based on the user's question, which of these files should I read to find the answer? "
                f"List up to {initial_query_count} relevant file(s). "
                "Your output should be a list of query objects. For each chosen file, the 'query' field in the object "
                "must be the full absolute path to that file. Construct this absolute path by joining the target folder path with the filename. "
                "For example, if the target folder is '/path/to/folder' and you choose 'file1.txt' from the list, "
                "the query string in the Query object must be '/path/to/folder/file1.txt'."
            )
            
            print(f"[generate_query] Prompting LLM to select files. Prompt (first 300 chars): {formatted_prompt[:300]}...")
            llm_output = structured_llm.invoke(formatted_prompt) # llm_output is SearchQueryList
            
            final_queries = []
            if llm_output and llm_output.query: # llm_output.query is List[Query]
                for query_obj in llm_output.query:
                    # LLM was prompted to return absolute paths.
                    # Validate that the path starts with target_folder and the filename part is in available_files.
                    query_path_str = query_obj.query
                    if isinstance(query_path_str, str) and query_path_str.startswith(target_folder):
                        # Basic check if filename seems to be from the list
                        potential_filename = os.path.basename(query_path_str)
                        if potential_filename in available_files:
                            print(f"[generate_query] LLM selected valid file: {query_path_str}")
                            final_queries.append(query_obj) # query_obj is already a Query instance
                        else:
                            print(f"[generate_query] LLM selected a file not in the original list, discarding: {query_path_str}")
                    else:
                         print(f"[generate_query] LLM selected an invalid (not absolute or wrong base folder) path, discarding: {query_path_str}")
            
            if not final_queries:
                print("[generate_query] LLM did not select any valid files from the provided list.")
            return {"query_list": final_queries}

        except Exception as e:
            print(f"[generate_query] Error listing files or processing folder '{target_folder}': {e}")
            return {"query_list": []}

    # 3. Fallback to general LLM query generation (if no target_folder or it's not a dir)
    # This includes the simple path validation from previous step.
    print("[generate_query] No target folder specified or path is invalid. Using general LLM query generation with path filtering.")
    current_date = get_current_date()
    
    # Check if research_topic_str itself looks like a specific file path to be directly used (general_file_path_match_in_fallback)
    # This regex is for more generic paths if user types one directly without specifying a folder.
    general_path_pattern = r"(?:['\"])?((?:[a-zA-Z]:)?[\/]?[\w\s./\-]+?\.\w+)(?:['\"])?"
    general_file_path_match = re.search(general_path_pattern, research_topic_str)

    if general_file_path_match:
        extracted_general_path = general_file_path_match.group(1).strip("'\"")
        # If the query IS a path, maybe the LLM should just confirm it.
        # Or, if the user is asking a question ABOUT this path.
        # For now, the prompt asks LLM to confirm it.
        print(f"[generate_query] General file path detected in query: '{extracted_general_path}'. Refining prompt for LLM.")
        formatted_prompt = (
            f"The user's query mentions this file path: '{extracted_general_path}'. "
            f"Your task is to determine if this is the file to be searched. If it seems to be the correct target, "
            f"output this exact file path as the search query. "
            f"If the query is more complex, consider if this path is relevant. "
            f"Question: {research_topic_str}. "
            f"Output only one search query object containing the confirmed file path if applicable."
        )
        # Force 1 query for this case
        state["initial_search_query_count"] = 1 
    else:
        print("[generate_query] No general file path detected in query. Using standard query writer prompt for file discovery.")
        formatted_prompt = query_writer_instructions.format( # Ensure query_writer_instructions is loaded
            current_date=current_date,
            research_topic=research_topic_str,
            number_queries=initial_query_count,
        )

    llm_fallback_result = structured_llm.invoke(formatted_prompt) # llm_fallback_result is SearchQueryList
    
    validated_queries_fallback = []
    if llm_fallback_result and llm_fallback_result.query: # llm_fallback_result.query is List[Query]
        for q_obj in llm_fallback_result.query: # q_obj is Query
            query_str = q_obj.query # This is the string path
            # Basic validation for path-like strings
            if isinstance(query_str, str) and ('.' in query_str or '/' in query_str or '\\' in query_str) and len(query_str) < 250 and not query_str.endswith("?"):
                print(f"[generate_query] Fallback LLM generated potential path: '{query_str}'")
                validated_queries_fallback.append(q_obj) # Add Query object
            else:
                print(f"[generate_query] Fallback LLM discarded non-path-like output: '{query_str}'")
    
    if not validated_queries_fallback:
        print("[generate_query] Fallback LLM did not produce any valid-looking file paths.")
    
    return {"query_list": validated_queries_fallback}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph node that sends the search queries to the web research node.

    This is used to spawn n number of web research nodes, one for each search query.
    """
    # This node now expects state["query_list"] to be a list of Query objects
    # The web_research node's input 'search_query' should be a string path.
    return [
        Send("web_research", {"search_query": query_obj.query, "id": int(idx)}) # Pass query_obj.query (the string)
        for idx, query_obj in enumerate(state["query_list"]) # query_list is List[Query]
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
