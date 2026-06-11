"""APNs device token registration."""

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceTokenIn(BaseModel):
    apns_token: str = Field(min_length=1, max_length=255)


@router.post("/apns", status_code=status.HTTP_204_NO_CONTENT)
async def register_apns_token(
    body: DeviceTokenIn,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> None:
    await db.execute(
        """INSERT INTO device_tokens (id, user_id, apns_token)
           VALUES ($1, $2, $3)
           ON CONFLICT ON CONSTRAINT uq_device_user_token DO NOTHING""",
        uuid.uuid4(),
        user["id"],
        body.apns_token,
    )
