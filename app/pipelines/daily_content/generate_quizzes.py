import logging

import httpx
from pydantic import BaseModel, ValidationError

from app.pipelines.daily_content.models import TalkItem
from app.services.gemma.complete_json import complete_json

logger = logging.getLogger(__name__)


class _QuizItem(BaseModel):
    question: str
    answer: str


class _QuizPayload(BaseModel):
    items: list[_QuizItem] = []


async def generate_quizzes(seed_titles: list[str]) -> list[TalkItem]:
    seed = (
        "\n".join(f"- {t}" for t in seed_titles[:5]) if seed_titles else "general everyday topics"
    )
    prompt = (
        "Generate 10 short English-conversation prompts (questions an English tutor would ask) "
        "with example answers. Seed topics:\n"
        f"{seed}\n\n"
        'Return JSON: {"items": [{"question": str, "answer": str}, ...]}.'
    )
    try:
        data = await complete_json(prompt)
    except httpx.HTTPError:
        logger.exception("generate_quizzes: gemma HTTP error")
        return []
    if not data:
        logger.warning("generate_quizzes: gemma returned empty / unparseable response")
        return []
    try:
        payload = _QuizPayload.model_validate(data)
    except ValidationError:
        logger.warning("generate_quizzes: payload shape mismatch, keys=%s", sorted(data.keys()))
        return []
    if not payload.items:
        logger.warning("generate_quizzes: items array empty in gemma response")
    return [
        TalkItem(title=it.question, summary=it.answer, source="", image_url="")
        for it in payload.items[:10]
    ]
