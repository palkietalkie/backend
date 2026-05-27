"""normalize_mistakes: filter LLM-emitted mistakes for shape + category + non-noop."""

from app.pipelines.mistake_detection.normalize_mistakes import normalize_mistakes


def test_normalize_mistakes_keeps_valid_record() -> None:
    out = normalize_mistakes(
        [
            {
                "original": "I have lived here since 5 years",
                "corrected": "I have lived here for 5 years",
                "category": "preposition",
            }
        ]
    )
    assert len(out) == 1
    assert out[0].category == "preposition"


def test_normalize_mistakes_drops_unknown_category() -> None:
    out = normalize_mistakes([{"original": "x", "corrected": "y", "category": "spelling"}])
    assert out == []


def test_normalize_mistakes_drops_when_original_equals_corrected() -> None:
    out = normalize_mistakes(
        [{"original": "same words", "corrected": "  same words  ", "category": "naturalness"}]
    )
    assert out == []


def test_normalize_mistakes_drops_malformed_items() -> None:
    out = normalize_mistakes(
        [
            "not a dict",
            {"original": "a", "corrected": "b"},
            {"category": "tense", "original": "a", "corrected": "b"},
        ]
    )
    assert len(out) == 1
    assert out[0].corrected == "b"


def test_normalize_mistakes_handles_empty_list() -> None:
    assert normalize_mistakes([]) == []
