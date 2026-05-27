import uuid
from typing import Any

import pytest

from app.services.neon.db_conn import DBConn


@pytest.fixture
async def apple_user(db: DBConn) -> dict[str, Any]:
    uid = uuid.uuid4()
    row = await db.fetchrow(
        """INSERT INTO users (id, clerk_user_id, premium)
           VALUES ($1, $2, FALSE)
           RETURNING id, clerk_user_id, premium, premium_ends_at""",
        uid,
        "user_apple_under_test",
    )
    assert row is not None
    return dict(row)
