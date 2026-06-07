from app.personas.voices.find_voice_by_id import find_voice_by_id
from app.personas.voices.list_voices_for_provider import list_voices_for_provider


def test_returns_voice_when_id_matches() -> None:
    voices = list_voices_for_provider("openai")
    if not voices:
        return
    needle = voices[0].id
    found = find_voice_by_id(needle, provider="openai")
    assert found is not None
    assert found.id == needle


def test_returns_none_for_unknown_id() -> None:
    assert find_voice_by_id("does-not-exist-voice", provider="openai") is None


def test_unknown_provider_returns_none() -> None:
    # list_voices_for_provider returns [] for unknown providers; lookup falls through.
    assert find_voice_by_id("anything", provider="not-a-real-provider") is None
