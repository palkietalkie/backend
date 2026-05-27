import httpx
from pydantic import BaseModel, ValidationError

from app.pipelines.daily_content.models import NewsStory, Quiz
from app.services.gemma.complete_json import complete_json


class _QuizItem(BaseModel):
    question: str
    answer: str


class _QuizPayload(BaseModel):
    items: list[_QuizItem] = []


async def generate_quizzes(news: list[NewsStory]) -> list[Quiz]:
    seed = "\n".join(f"- {n.title}" for n in news[:5]) if news else "general everyday topics"
    prompt = (
        "Generate 10 short English-conversation prompts (questions an English tutor would ask) "
        "with example answers. Seed topics:\n"
        f"{seed}\n\n"
        'Return JSON: {"items": [{"question": str, "answer": str}, ...]}.'
    )
    try:
        data = await complete_json(prompt)
    except httpx.HTTPError:
        return []
    try:
        payload = _QuizPayload.model_validate(data)
    except ValidationError:
        return []
    return [Quiz(question=it.question, answer=it.answer) for it in payload.items[:10]]
