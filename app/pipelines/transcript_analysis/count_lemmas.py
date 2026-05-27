from app.pipelines.transcript_analysis.lemmatize import lemmatize


def count_lemmas(texts: list[str]) -> dict[str, int]:
    # Pure tokenize + lemmatize + tally. No DB, no LLM.
    counts: dict[str, int] = {}
    for text in texts:
        for lemma in lemmatize(text):
            counts[lemma] = counts.get(lemma, 0) + 1
    return counts
