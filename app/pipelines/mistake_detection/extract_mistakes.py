import httpx

from app.pipelines.mistake_detection.build_prompt import build_prompt
from app.pipelines.mistake_detection.mistake_record import MistakeRecord
from app.pipelines.mistake_detection.normalize_mistakes import normalize_mistakes
from app.services.gemma.complete_json import complete_json


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
    return normalize_mistakes(list(data.get("mistakes") or []))
