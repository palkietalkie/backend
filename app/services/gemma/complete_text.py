import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.services.gemma.constants import (
    DEFAULT_MODEL,
    ENDPOINT_TEMPLATE,
    GEMMA_TIMEOUT_SECONDS,
)


class _Part(BaseModel):
    text: str = ""
    # Gemma 4 emits the model's internal reasoning as a separate part with thought=true. Skip those at concat time so the JSON parser doesn't see prose-formatted "thinking" mixed in with the actual response.
    thought: bool = False


class _Content(BaseModel):
    parts: list[_Part] = []


class _Candidate(BaseModel):
    content: _Content | None = None


class _GemmaResponse(BaseModel):
    candidates: list[_Candidate] = []


async def complete_text(prompt: str, *, system: str | None = None) -> str:
    # Gemma's generateContent endpoint doesn't accept a separate system_instruction the way Gemini does, so prepend the system prompt to the user message.
    settings = get_settings()
    if not settings.gemini_api_key:
        # No key configured — return empty so pipelines treat this as "no findings" rather than failing the request.
        return ""

    user_text = prompt
    if system:
        user_text = f"{system}\n\n{prompt}"
    else:
        user_text = "You are a precise English-learning analysis assistant.\n\n" + prompt

    # No maxOutputTokens: free tier, verified via API probe that the field is optional and the model stops on its own (finishReason: STOP). Capping it was the bug behind quizzes=0.
    body = {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.2},
    }
    url = ENDPOINT_TEMPLATE.format(model=DEFAULT_MODEL)
    params = {"key": settings.gemini_api_key}

    async with httpx.AsyncClient(timeout=GEMMA_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, params=params, json=body)
        resp.raise_for_status()
        data = resp.json()

    try:
        parsed = _GemmaResponse.model_validate(data)
    except ValidationError:
        return ""
    if not parsed.candidates or parsed.candidates[0].content is None:
        return ""
    return "".join(p.text for p in parsed.candidates[0].content.parts if not p.thought).strip()
