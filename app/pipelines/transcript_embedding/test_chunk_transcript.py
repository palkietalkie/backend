from app.pipelines.transcript_embedding.chunk_transcript import chunk_transcript


def test_empty_returns_no_chunks() -> None:
    assert chunk_transcript([]) == []


def test_short_transcript_is_one_chunk_with_speaker_labels() -> None:
    out = chunk_transcript([("user", "hi"), ("persona", "hello there")])
    assert out == ["user: hi\npersona: hello there"]


def test_splits_into_windows_without_breaking_turns() -> None:
    turns = [("user", "a" * 600), ("persona", "b" * 600), ("user", "c" * 600)]
    chunks = chunk_transcript(turns, max_chars=1000)
    # 3 turns of ~606 chars each: turn1+turn2 would exceed 1000, so each turn lands in its own window.
    assert len(chunks) == 3
    # No turn is split mid-text.
    assert chunks[0] == f"user: {'a' * 600}"
    assert chunks[1] == f"persona: {'b' * 600}"
