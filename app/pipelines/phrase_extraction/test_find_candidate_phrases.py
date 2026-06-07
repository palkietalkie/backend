from app.pipelines.phrase_extraction.find_candidate_phrases import find_candidate_phrases


def test_empty_input_returns_empty_list() -> None:
    assert find_candidate_phrases([]) == []


def test_skips_phrases_with_stopword_edges() -> None:
    # "the cat" starts with a stopword → suppressed. "cat sat" survives if it occurs ≥ twice.
    out = find_candidate_phrases(["cat sat there", "cat sat happily"], top_k=20)
    out_phrases = {p for p, _c in out}
    assert "cat sat" in out_phrases
    # Stopword-edged phrases should not appear.
    assert all(not p.startswith("the ") and not p.endswith(" the") for p, _ in out)


def test_requires_minimum_count_of_two() -> None:
    # A phrase that appears only once doesn't make the cut.
    out = find_candidate_phrases(["this is a single appearance"], top_k=20)
    assert out == []


def test_respects_top_k() -> None:
    out = find_candidate_phrases(["cat sat there", "cat sat happily"] * 5, top_k=1)
    assert len(out) <= 1
