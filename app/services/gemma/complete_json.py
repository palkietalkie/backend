import json
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.services.gemma.complete_text import complete_text

_DICT_ADAPTER: TypeAdapter[dict[str, Any]] = TypeAdapter(dict[str, Any])


def _try_load(text: str) -> dict[str, Any]:
    try:
        return _DICT_ADAPTER.validate_python(json.loads(text))
    except json.JSONDecodeError, ValidationError:
        return {}


async def complete_json(
    prompt: str, *, system: str | None = None, max_tokens: int = 1024
) -> dict[str, Any]:
    # On parse failure, return an empty dict instead of raising — pipelines should treat that as "no findings".
    text = await complete_text(prompt, system=system, max_tokens=max_tokens)
    if not text:
        return {}
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    out = _try_load(text)
    if out:
        return out
    # Last-resort: extract first balanced { ... } block.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return _try_load(text[start : end + 1])
    return {}
