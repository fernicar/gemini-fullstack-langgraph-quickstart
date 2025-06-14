from typing import List
from pydantic import BaseModel, Field


class Query(BaseModel):
    query: str = Field(description="A specific search query string.")
    rationale: str = Field(default="", description="Rationale for why this specific query is useful.")


class SearchQueryList(BaseModel):
    # query: List[str] = Field( # Changed from List[str]
    query: List[Query] = Field( # Now a list of Query objects
        description="A list of search query objects to be used for web research."
    )
    rationale: str = Field( # This rationale applies to the overall list generation process
        default="", # Provide a default if it can sometimes be omitted by the LLM
        description="A brief explanation of why these queries (as a whole set) are relevant to the research topic."
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the provided summaries are sufficient to answer the user's question."
    )
    knowledge_gap: str = Field(
        description="A description of what information is missing or needs clarification."
    )
    follow_up_queries: List[str] = Field(
        description="A list of follow-up queries to address the knowledge gap."
    )
