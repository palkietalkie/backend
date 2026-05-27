import httpx

from app.config import get_settings
from app.services.gemma.constants import (
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT_TEMPLATE,
)


async def complete_text(
    prompt: str, *, system: str | None = None, max_tokens: int = 1024
) -> str:
    # Gemma's generateContent endpoint doesn't accept a separate system_instruction the way Gemini does, so prepend the system prompt to the user message.
    settings = get_settings()
    if not settings.gemini_api_key:
        # No key configured — return empty so pipelines treat this as "no findings" rather than failing the request.
        return ""

    user_text = prompt
    if system:
        user_text = f"{system}\n\n{prompt}"
    else:
        user_text = (
            "You are a precise English-learning analysis assistant.\n\n" + prompt
        )

    body = {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2,
        },
    }
    url = ENDPOINT_TEMPLATE.format(model=DEFAULT_MODEL)
    params = {"key": settings.gemini_api_key}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
        resp = await client.post(url, params=params, json=body)
        resp.raise_for_status()
        data = resp.json()

    try:
        parts = data["candidates"][0]["content"]["parts"]
    except KeyError, IndexError, TypeError:
        return ""
    out: list[str] = []
    for part in parts:
        text = part.get("text") if isinstance(part, dict) else None
        if isinstance(text, str):
            out.append(text)
    return "".join(out).strip()
