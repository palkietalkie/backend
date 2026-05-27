"""Lazy spaCy model load. Falls back to None if model unavailable so CI can run without the 12MB en_core_web_sm download."""

from typing import Any


def _load() -> Any:
    try:
        import spacy

        return spacy.load("en_core_web_sm", disable=["ner", "parser"])
    except ImportError, OSError:
        # ImportError: spacy not installed (rare). OSError: model not downloaded (dev).
        return None


nlp: Any = _load()
