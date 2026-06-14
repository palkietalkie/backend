def chunk_transcript(turns: list[tuple[str, str]], max_chars: int = 1500) -> list[str]:
    """Group consecutive turns into ~max_chars windows for embedding. Turns are kept whole (never split mid-turn) so each chunk reads as coherent dialogue; the embedding model has a token cap, so one giant blob would be truncated and lose the tail. A single turn longer than max_chars becomes its own (over-cap) chunk — Pinecone truncates that one, and keyword search still covers it verbatim."""
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for speaker, text in turns:
        line = f"{speaker}: {text}"
        if current and size + len(line) > max_chars:
            chunks.append("\n".join(current))
            current = []
            size = 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks
