from collections import Counter

from app.post_session_nlp.phrase_extraction.build_ngrams import build_ngrams
from app.post_session_nlp.phrase_extraction.constants import STOPWORDS
from app.post_session_nlp.phrase_extraction.tokenize import tokenize


def find_candidate_phrases(texts: list[str], top_k: int = 50) -> list[tuple[str, int]]:
    # Pure n-gram candidate phrase extraction. No LLM, no DB.
    counter: Counter[str] = Counter()
    for text in texts:
        toks = tokenize(text)
        for n in (2, 3, 4):
            for ng in build_ngrams(toks, n):
                parts = ng.split()
                if parts[0] in STOPWORDS or parts[-1] in STOPWORDS:
                    continue
                counter[ng] += 1
    return [(p, c) for p, c in counter.most_common(top_k) if c >= 2]
