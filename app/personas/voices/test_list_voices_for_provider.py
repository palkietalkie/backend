from app.personas.voices.list_voices_for_provider import list_voices_for_provider
from app.personas.voices.openai_voices import OPENAI_VOICES
from app.personas.voices.personaplex_voices import PERSONAPLEX_VOICES


def test_openai_gets_the_openai_catalog() -> None:
    assert list_voices_for_provider("openai") == OPENAI_VOICES


def test_openai_webrtc_shares_the_openai_catalog() -> None:
    # Regression: openai_webrtc fell through to PersonaPlex voices, which then failed OpenAIVoiceId validation and 400'd /conversation/start on the WebRTC path.
    assert list_voices_for_provider("openai_webrtc") == OPENAI_VOICES


def test_personaplex_gets_the_personaplex_catalog() -> None:
    assert list_voices_for_provider("personaplex") == PERSONAPLEX_VOICES
