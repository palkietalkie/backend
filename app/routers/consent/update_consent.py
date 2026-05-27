from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.routers.consent.fetch_consent import ConsentOut
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentUpdate(BaseModel):
    personalization: bool
    product_improvement: bool


@router.put("", response_model=ConsentOut)
async def update_consent(
    body: ConsentUpdate,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> ConsentOut:
    now = datetime.now(UTC)
    await db.execute(
        """UPDATE users
           SET personalization_consent     = $2,
               product_improvement_consent = $3,
               consent_screen_seen_at      = COALESCE(consent_screen_seen_at, $4),
               updated_at                  = NOW()
           WHERE id = $1""",
        user["id"],
        now if body.personalization else None,
        now if body.product_improvement else None,
        now,
    )
    return ConsentOut(
        personalization=body.personalization,
        product_improvement=body.product_improvement,
        set=True,
    )
