from typing import Any

from app.services.openai.realtime_tools import REALTIME_TOOLS


def _by_name(name: str) -> dict[str, Any] | None:
    return next((t for t in REALTIME_TOOLS if t["name"] == name), None)


def test_all_tools_are_well_formed_function_tools() -> None:
    # A malformed tool dict breaks the realtime session mint, so lock the shape every tool must have.
    for tool in REALTIME_TOOLS:
        assert tool["type"] == "function"
        assert isinstance(tool["name"], str) and tool["name"]
        assert isinstance(tool["description"], str) and tool["description"]
        params = tool["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params


def test_expected_tools_are_present() -> None:
    names = {t["name"] for t in REALTIME_TOOLS}
    assert names == {
        "recall_facts",
        "recall_past_conversations",
        "search_transcripts",
        "web_fetch",
        "end_conversation",
    }


def test_end_conversation_only_ends_on_an_explicit_user_farewell() -> None:
    # Locks the fix for the premature-hang-up bug: the model must require an EXPLICIT user farewell and must NOT end on its own judgement or on a topical remark (the exact false positive that ended a live session: "no unfinished business").
    tool = _by_name("end_conversation")
    assert tool is not None
    desc = tool["description"].lower()
    assert "explicit" in desc
    assert "never end" in desc or "do not end" in desc
    assert "unfinished business" in desc
