import re

from app.pipelines.transcript_analysis import _nlp

_WORD_RE = re.compile(r"[A-Za-z']+")


def lemmatize(text: str) -> list[str]:
    if _nlp.nlp is None:
        return [w.lower() for w in _WORD_RE.findall(text)]
    doc = _nlp.nlp(text)
    return [
        tok.lemma_.lower()
        for tok in doc
        if tok.is_alpha and not tok.is_stop and len(tok.lemma_) > 1
    ]
