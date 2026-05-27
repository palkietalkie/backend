import uuid

import pytest


@pytest.fixture
async def apple_user(db) -> dict:
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
