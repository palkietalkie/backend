import json

from app.services.gemma.complete_text import complete_text


async def complete_json(prompt: str, *, system: str | None = None, max_tokens: int = 1024) -> dict:
    # On parse failure, return an empty dict instead of raising — pipelines should treat that as "no findings".
    text = await complete_text(prompt, system=system, max_tokens=max_tokens)
    if not text:
        return {}
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else {}
    except json.JSONDecodeError:
        # Last-resort: extract first balanced { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            try:
                loaded = json.loads(text[start : end + 1])
                return loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError:
                pass
        return {}
