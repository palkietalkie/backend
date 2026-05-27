"""In-process per-date cache for compose_today_content. One Fly instance at $5 tier so a dict is fine; move to Redis / Postgres if we scale out."""

from datetime import date

from app.pipelines.daily_content.models import DailyContent

CACHE: dict[date, DailyContent] = {}
