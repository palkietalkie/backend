from app.pipelines.transcript_analysis.count_lemmas import count_lemmas


def test_empty_input_returns_empty_dict() -> None:
    assert count_lemmas([]) == {}


def test_counts_repeated_lemmas_across_texts() -> None:
    counts = count_lemmas(["the cat sat", "the cat ran"])
    # spaCy lemmatization collapses "sat"/"ran" to "sit"/"run" etc, but "cat" remains "cat" and appears in both inputs.
    assert counts.get("cat", 0) >= 2


def test_single_text_tallied_once_per_occurrence() -> None:
    counts = count_lemmas(["walk walk walk"])
    assert counts.get("walk", 0) == 3
