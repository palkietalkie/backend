"""'What to talk about today' screen (Feature 4): pre-fetched per-topic sections.

Reads from the `daily_content` table populated by `run_daily_content_scheduler` (in-process daily cron at 06:00 UTC). Never calls upstream APIs (NewsAPI, Gemma) at request time.

News topics (politics/business/sports) return today's row only — those are time-sensitive. Pool topics (quizzes) are timeless; the router aggregates ALL historical items for that topic and samples deterministically with today's date as the RNG seed, so users see a rotating cut across days without burning per-day generation cost."""

import random
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.pipelines.daily_content.constants import POOL_SAMPLE_SIZE, POOL_TOPICS, TOPICS
from app.pipelines.daily_content.models import TalkItem
from app.services.daily_content.load_today_topics import load_today_topics
from app.services.daily_content.load_topic_pool import load_topic_pool
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/content", tags=["content"])


class ItemOut(BaseModel):
    title: str
    summary: str
    source: str
    image_url: str


class SectionOut(BaseModel):
    topic: str
    items: list[ItemOut]


class DailyContentResponse(BaseModel):
    day: date
    sections: list[SectionOut]


def _sample_pool(pool: list[TalkItem], seed: str, k: int) -> list[TalkItem]:
    if not pool:
        return []
    # noqa: S311 — deterministic sampling of timeless content (quizzes) keyed on the date string. Not used for any security/crypto purpose; the seed is public-facing (today's date). secrets.SystemRandom would defeat the determinism we want here (same date → same sample for all users).
    rng = random.Random(seed)  # noqa: S311
    return rng.sample(pool, min(k, len(pool)))


@router.get("/today", response_model=DailyContentResponse)
async def fetch_today_content(
    _user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> DailyContentResponse:
    today = datetime.now(UTC).date()
    today_topics = await load_today_topics(db)

    sections: list[SectionOut] = []
    for topic in TOPICS:
        if topic in POOL_TOPICS:
            pool = await load_topic_pool(topic, db)
            items = _sample_pool(pool, today.isoformat(), POOL_SAMPLE_SIZE)
        else:
            items = today_topics.get(topic, [])
        sections.append(
            SectionOut(
                topic=topic,
                items=[
                    ItemOut(
                        title=i.title,
                        summary=i.summary,
                        source=i.source,
                        image_url=i.image_url,
                    )
                    for i in items
                ],
            )
        )
    return DailyContentResponse(day=today, sections=sections)
