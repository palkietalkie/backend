import re

_WORD_RE = re.compile(r"[A-Za-z']+")


def tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]
