import httpx
from pydantic import BaseModel, ValidationError

from app.post_session_nlp.mistake_detection.build_prompt import build_prompt
from app.post_session_nlp.mistake_detection.mistake_record import MistakeRecord
from app.post_session_nlp.mistake_detection.normalize_mistakes import normalize_mistakes
from app.services.gemma.complete_json import complete_json


class _MistakeBatch(BaseModel):
    # Permissive — normalize_mistakes does the field-level filtering. Here we just lift the LLM JSON into a real list[dict[str, object]] so pyright can see typed values flow downstream.
    mistakes: list[dict[str, object]] = []


async def extract_mistakes(texts: list[str]) -> list[MistakeRecord]:
    # LLM-only mistake extraction. Returns empty list on outage or no findings.
    if not texts:
        return []
    turns = "\n".join(f"- {t}" for t in texts)
    prompt = build_prompt(turns)
    try:
        data = await complete_json(prompt)
    except httpx.HTTPError:
        return []
    try:
        batch = _MistakeBatch.model_validate(data)
    except ValidationError:
        return []
    items: list[object] = list(batch.mistakes)
    return normalize_mistakes(items)
