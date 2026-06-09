"""Lock in the OpenAI Realtime voice catalog: every entry must have a unique id, a non-empty label, and one of the three gender slots iOS expects."""

from app.personas.voices.openai_voices import OPENAI_VOICES


def test_voices_have_unique_ids() -> None:
    ids = [v.id for v in OPENAI_VOICES]
    assert len(ids) == len(set(ids)), f"duplicate voice ids in OPENAI_VOICES: {ids}"


def test_voices_have_non_empty_labels_and_descriptions() -> None:
    for v in OPENAI_VOICES:
        assert v.label.strip(), f"voice {v.id} has empty label"
        assert v.description.strip(), f"voice {v.id} has empty description"


def test_voices_gender_slot_is_one_of_the_three_ios_expects() -> None:
    for v in OPENAI_VOICES:
        assert v.gender in {"male", "female", "neutral"}, f"voice {v.id} bad gender {v.gender!r}"


def test_catalog_is_not_empty() -> None:
    assert len(OPENAI_VOICES) > 0
