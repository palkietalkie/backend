"""In-app "rate your experience" submission.

A typed home for the rating prompt's result, separate from the generic `events` telemetry sink: the rating is a constrained column (1-5) with a real user FK, so it can be queried and aggregated directly. We collect a comment from every rating (happy users included), not just unhappy ones."""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.slack.format_user_label import format_user_label
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/ratings", tags=["ratings"])


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def record_experience_rating(
    body: RatingIn,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> None:
    await db.execute(
        """INSERT INTO experience_ratings (user_id, rating, comment)
           VALUES ($1, $2, $3)""",
        user["id"],
        body.rating,
        body.comment,
    )

    # Slack the rating live from production only: an early qualitative signal a human wants to see now. Dev shares the same Slack creds, so unfiltered every connected-device test would spam the channel.
    settings = get_settings()
    if settings.app_env == "production":
        stars = "★" * body.rating + "☆" * (5 - body.rating)
        text = f":star: *{stars}* ({body.rating}/5) {format_user_label(user)}"
        if body.comment:
            text += f"\n> {body.comment}"
        await post_message(settings.slack_channel_gtm, text)
