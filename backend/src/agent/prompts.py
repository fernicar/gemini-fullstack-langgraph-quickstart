from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """Your goal is to identify relevant project files for a given research topic. These files will be used by an automated tool to gather information for narrative storytelling, adhering to writing rules contained within the project.

Instructions:
- Based on the 'research_topic', identify specific file paths within the project that are likely to contain relevant information or writing rules.
- Always prefer a single file path if it seems most relevant, only add more paths if the topic requires information from multiple files (e.g., a content file and a rules file).
- If the research topic involves content creation, narrative writing, or style adherence, actively look for files that seem to define writing rules, style guides, or formatting instructions (e.g., 'style_guide.md', 'rules/formatting.txt', 'narrative_voice.txt'). These are as important as content files.
- Don't produce more than {number_queries} file paths.
- If the topic is broad, identify multiple relevant files.
- File paths should be relative to the project root (e.g., "data/narrative_chapter1.txt", "rules/style_guide.md").
- Consider common file extensions for text or markdown files like .txt, .md.

Format:
- Format your response as a JSON object with ALL three of these exact keys:
  - "rationale": Brief explanation of why these files are relevant to the research topic.
  - "query": A list of file paths (strings).

Example:

Topic: "Gather information about the protagonist's background and the project's style guide for dialogue."
```json
{{
    "rationale": "To address the topic, we need the protagonist's background information, likely in a character bio file, and the dialogue style rules from the project's style guide.",
    "query": ["characters/protagonist_bio.txt", "writing_rules/dialogue_style.md"]
}}
```

Context: {research_topic}"""


web_searcher_instructions = """Conduct targeted Google Searches to gather the most recent, credible information on "{research_topic}" and synthesize it into a verifiable text artifact.

Instructions:
- Query should ensure that the most current information is gathered. The current date is {current_date}.
- Conduct multiple, diverse searches to gather comprehensive information.
- Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
- The output should be a well-written summary or report based on your search findings. 
- Only include the information found in the search results, don't make up any information.

Research Topic:
{research_topic}
"""

reflection_instructions = """You are an expert research assistant analyzing summaries about "{research_topic}".

Instructions:
- Identify knowledge gaps or areas that need deeper exploration and generate a follow-up query. (1 or multiple).
- If provided summaries are sufficient to answer the user's question, don't generate a follow-up query.
- If there is a knowledge gap, generate a follow-up query that would help expand your understanding.
- Focus on technical details, implementation specifics, or emerging trends that weren't fully covered.

Requirements:
- Ensure the follow-up query is self-contained and includes necessary context for web search.

Output Format:
- Format your response as a JSON object with these exact keys:
   - "is_sufficient": true or false
   - "knowledge_gap": Describe what information is missing or needs clarification
   - "follow_up_queries": Write a specific question to address this gap

Example:
```json
{{
    "is_sufficient": true, // or false
    "knowledge_gap": "The summary lacks information about performance metrics and benchmarks", // "" if is_sufficient is true
    "follow_up_queries": ["What are typical performance benchmarks and metrics used to evaluate [specific technology]?"] // [] if is_sufficient is true
}}
```

Reflect carefully on the Summaries to identify knowledge gaps and produce a follow-up query. Then, produce your output following this JSON format:

Summaries:
{summaries}
"""

answer_instructions = """Generate a high-quality answer (e.g., narrative text, story elements) to the user's research topic, strictly adhering to any specified writing rules found in the provided project files.

Instructions:
- You are the final step of a multi-step process. Your response should be a comprehensive answer or generated content as per the user's query.
- The "File Contents (Summaries)" you receive ({summaries}) contain the full text of various project files. Some of these files might be data or content (e.g., character sheets, plot points), while others might be WRITING RULES or STYLE GUIDES (e.g., style_guide.md, voice_and_tone.txt).
- **Identify Writing Rules**: Carefully examine the provided file contents. If any files appear to define writing rules, styles, formatting guidelines, or a specific narrative voice, you MUST identify and understand these rules.
- **Strict Adherence**: Your primary goal is to generate a response that not only uses the content files but also STRICTLY ADHERES to all identified writing rules. This includes, but is not limited to, dialogue formatting, tone, style, character voice, and any other constraints mentioned in the rule files.
- **Citations**: When you use information from a content file, or when your writing is directly influenced by a rule file, you MUST cite the file path. Use a clear and consistent citation format, for example: "[Source: path/to/your/file.txt]" for content or "[Style Ref: path/to/rules.txt]" for rules.
- **Address Research Topic**: Ensure your answer directly addresses the user's research topic, using information from the provided content files and shaped by the writing rules.
- **No External Information**: Do not make up information or rules. Base your answer strictly on the content of the provided files. If rules are ambiguous or conflicting, note this in your response if appropriate, or make a best-effort interpretation.

User Context (Research Topic):
- {research_topic}

File Contents (Summaries):
{summaries}"""
