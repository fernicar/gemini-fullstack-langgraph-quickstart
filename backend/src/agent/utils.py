from typing import Any, Dict, List # List is already here
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from pathlib import Path
import os # os is already here


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """
    Create a map of the vertex ai search urls (very long) to a short url with a unique id for each url.
    Ensures each original URL gets a consistent shortened form while maintaining uniqueness.
    """
    prefix = f"https://vertexaisearch.cloud.google.com/id/"
    urls = [site.web.uri for site in urls_to_resolve]

    # Create a dictionary that maps each unique URL to its first occurrence index
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted.
    """
    # Sort citations by end_index in descending order.
    # If end_index is the same, secondary sort by start_index descending.
    # This ensures that insertions at the end of the string don't affect
    # the indices of earlier parts of the string that still need to be processed.
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        # These indices refer to positions in the *original* text,
        # but since we iterate from the end, they remain valid for insertion
        # relative to the parts of the string already processed.
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        # Insert the citation marker at the original end_idx position
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    Extracts and formats citation information from a Gemini model's response.

    This function processes the grounding metadata provided in the response to
    construct a list of citation objects. Each citation object includes the
    start and end indices of the text segment it refers to, and a string
    containing formatted markdown links to the supporting web chunks.

    Args:
        response: The response object from the Gemini model, expected to have
                  a structure including `candidates[0].grounding_metadata`.
                  It also relies on a `resolved_map` being available in its
                  scope to map chunk URIs to resolved URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a citation
              and has the following keys:
              - "start_index" (int): The starting character index of the cited
                                     segment in the original text. Defaults to 0
                                     if not specified.
              - "end_index" (int): The character index immediately after the
                                   end of the cited segment (exclusive).
              - "segments" (list[str]): A list of individual markdown-formatted
                                        links for each grounding chunk.
              - "segment_string" (str): A concatenated string of all markdown-
                                        formatted links for the citation.
              Returns an empty list if no valid candidates or grounding supports
              are found, or if essential data is missing.
    """
    citations = []

    # Ensure response and necessary nested structures are present
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # Ensure segment information is present
        if not hasattr(support, "segment") or support.segment is None:
            continue  # Skip this support if segment info is missing

        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # Ensure end_index is present to form a valid segment
        if support.segment.end_index is None:
            continue  # Skip if end_index is missing, as it's crucial

        # Add 1 to end_index to make it an exclusive end for slicing/range purposes
        # (assuming the API provides an inclusive end_index)
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],
                            "short_url": resolved_url,
                            "value": chunk.web.uri,
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # Handle cases where chunk, web, uri, or resolved_map might be problematic
                    # For simplicity, we'll just skip adding this particular segment link
                    # In a production system, you might want to log this.
                    pass
        citations.append(citation)
    return citations


def read_project_file(file_path_query: str, node_id: int) -> dict:
    # Assuming utils.py is in backend/src/agent/
    # Path(__file__) is /app/backend/src/agent/utils.py
    # parents[0] is /app/backend/src/agent
    # parents[1] is /app/backend/src
    # parents[2] is /app/backend
    # parents[3] is /app (project root)
    project_root = Path(__file__).resolve().parents[3]
    actual_file_path = project_root / file_path_query.strip("'\"") # Clean potential quotes

    print(f"[read_project_file] Received query: '{file_path_query}'")
    print(f"[read_project_file] Node ID: {node_id}")
    print(f"[read_project_file] Project root: '{project_root}'")
    print(f"[read_project_file] Attempting to read: '{actual_file_path}'")

    try:
        # Use actual_file_path for reading
        with open(actual_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        print(f"[read_project_file] Successfully read file: '{actual_file_path}'")
        return {
            "sources_gathered": [{"type": "file", "source": str(actual_file_path), "content": file_content, "id": node_id}],
            "web_research_result": [file_content]
        }
    except FileNotFoundError:
        error_message = f"File not found: {str(actual_file_path)}"
        print(f"[read_project_file] Error: {error_message}")
        return {
            "sources_gathered": [{"type": "file", "source": str(actual_file_path), "content": error_message, "id": node_id, "error": True}],
            "web_research_result": [error_message]
        }
    except Exception as e:
        error_message = f"Error reading file {str(actual_file_path)}: {str(e)}"
        print(f"[read_project_file] Error: {error_message}")
        return {
            "sources_gathered": [{"type": "file", "source": str(actual_file_path), "content": error_message, "id": node_id, "error": True}],
            "web_research_result": [error_message]
        }


# list_files_in_directory is not requested to be moved here unless needed by agent logic.
# The graph.py's CLI test part was modified to import it from utils if needed, or use direct os.listdir.
# For now, not adding list_files_in_directory to utils.py as it's not part of the core agent flow modifications.

def list_files_in_directory(folder_path: str) -> List[str]:
    """
    Lists all filenames (not full paths) in a given directory.
    Excludes hidden files/folders (those starting with '.').
    Returns an empty list if the path is not a directory or is inaccessible.
    """
    if not folder_path or not os.path.isdir(folder_path):
        print(f"[list_files_in_directory] Path is not a valid directory or is empty: '{folder_path}'")
        return []
    try:
        entries = os.listdir(folder_path)
        # Filter out hidden files/directories and return only files
        files = [
            f for f in entries
            if not f.startswith('.') and os.path.isfile(os.path.join(folder_path, f))
        ]
        print(f"[list_files_in_directory] Found files in '{folder_path}': {files}")
        return files
    except OSError as e: # Catch potential OS errors like permission denied
        print(f"[list_files_in_directory] Error listing files in '{folder_path}': {e}")
        return []
    except Exception as e: # Catch any other unexpected errors
        print(f"[list_files_in_directory] Unexpected error for path '{folder_path}': {e}")
        return []
