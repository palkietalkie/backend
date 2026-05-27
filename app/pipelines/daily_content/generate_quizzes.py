import httpx

from app.pipelines.daily_content.models import NewsStory, Quiz
from app.services.gemma.complete_json import complete_json


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
    items = data.get("items") or []
    quizzes: list[Quiz] = []
    for it in items[:10]:
        q = it.get("question") if isinstance(it, dict) else None
        a = it.get("answer") if isinstance(it, dict) else None
        if isinstance(q, str) and isinstance(a, str):
            quizzes.append(Quiz(question=q, answer=a))
    return quizzes
