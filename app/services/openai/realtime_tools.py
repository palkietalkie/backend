"""OpenAI Realtime function tools the model can call mid-conversation.

All tools are defined the same way through `_tool`: recall_* are answered by iOS against /recall/*, web_fetch reads a URL via /recall/web_fetch, and end_conversation is a pure hang-up signal iOS acts on. iOS feeds each result back asynchronously so audio never blocks. PersonaPlex has no function calling, so these only apply on the OpenAI path.
"""

from typing import Any


def _tool(
    name: str, description: str, properties: dict[str, Any], required: list[str]
) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required},
    }


_QUERY = {"query": {"type": "string", "description": "What to look up, in a few words."}}

REALTIME_TOOLS: list[dict[str, Any]] = [
    _tool(
        "recall_facts",
        "Look up a structured fact about the user, a person, place, project, or interest they mentioned before (who someone is, where they work). Use when you need who/what/where about someone in their life.",
        _QUERY,
        ["query"],
    ),
    _tool(
        "recall_past_conversations",
        "Recall what you and the user talked about in earlier sessions that relates to the current topic. Use when the conversation echoes something from before.",
        _QUERY,
        ["query"],
    ),
    _tool(
        "search_transcripts",
        "Search the user's exact past words for a specific term or phrase, when you need what they literally said rather than a paraphrase.",
        _QUERY,
        ["query"],
    ),
    _tool(
        "web_fetch",
        "Fetch a public web page by URL and read its text, to ground yourself in real, current facts instead of guessing. Use it the moment the conversation turns on something specific and current you should NOT invent: a score, a ranking, a release date, a price, a news detail. Pass a real https URL you are confident exists. Better to fetch and be accurate than to confabulate.",
        {"url": {"type": "string", "description": "The full public https URL to fetch."}},
        ["url"],
    ),
    _tool(
        "end_conversation",
        "End the conversation and return the user to the app. ONLY call this when the USER has EXPLICITLY asked to stop talking, with an unambiguous farewell: 'I have to go', 'let's stop', 'bye', 'talk later', 'that's all for today', or the clear equivalent in their language. Say one short goodbye line, then call this. NEVER end on your own judgement that the chat has wound down, on a pause or thinking silence, or on a remark about the TOPIC rather than the conversation — e.g. 'there's nothing left between us', 'no unfinished business', 'we're done with that', 'that settles it' are about the subject, NOT a request to leave, so keep going and ask a follow-up. When in doubt, do NOT end. A conversation cut off while the user still wants to talk is far worse than one that runs a little long.",
        {},
        [],
    ),
]
