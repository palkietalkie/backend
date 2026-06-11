"""OpenAI Realtime tool definitions for conversation-time memory recall.

The model calls these itself when the topic calls for it — recall is topic-driven and on-demand (the human-brain model), not pre-loaded into the prompt. iOS handles each call against the backend /recall/* endpoints and feeds the result back asynchronously, so audio never blocks. PersonaPlex has no function calling, so these only apply on the OpenAI path.
"""

from typing import Any


def _recall_tool(name: str, description: str) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to look up, in a few words."}
            },
            "required": ["query"],
        },
    }


RECALL_TOOLS: list[dict[str, Any]] = [
    _recall_tool(
        "recall_facts",
        "Look up a structured fact about the user — a person, place, project, or interest they mentioned before (who someone is, where they work). Use when you need who/what/where about someone in their life.",
    ),
    _recall_tool(
        "recall_past_conversations",
        "Recall what you and the user talked about in earlier sessions that relates to the current topic. Use when the conversation echoes something from before.",
    ),
    _recall_tool(
        "search_transcripts",
        "Search the user's exact past words for a specific term or phrase, when you need what they literally said rather than a paraphrase.",
    ),
]
