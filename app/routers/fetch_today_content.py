"""'What to talk about today' screen (Feature 4): 10 news + 10 quizzes."""

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.pipelines.daily_content.compose_today_content import compose_today_content
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/content", tags=["content"])


class NewsOut(BaseModel):
    title: str
    description: str
    url: str
    source: str


class QuizOut(BaseModel):
    question: str
    answer: str


class DailyContentResponse(BaseModel):
    day: date
    news: list[NewsOut]
    quizzes: list[QuizOut]


@router.get("/today", response_model=DailyContentResponse)
async def fetch_today_content(
    _user: UserRow = Depends(resolve_current_user),
) -> DailyContentResponse:
    content = await compose_today_content()
    return DailyContentResponse(
        day=content.day,
        news=[NewsOut(**n.__dict__) for n in content.news],
        quizzes=[QuizOut(**q.__dict__) for q in content.quizzes],
    )
