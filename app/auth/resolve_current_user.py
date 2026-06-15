"""FastAPI dependency: verify the bearer JWT and load the matching User row, creating it on first sight."""

import uuid

from fastapi import Depends, Header, HTTPException, status

from app.auth.extract_bearer import extract_bearer
from app.auth.verify_clerk_jwt import verify_clerk_jwt
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.make_rows import make_user_row
from app.services.neon.rows import UserRow


async def resolve_current_user(
    authorization: str | None = Header(default=None),
    db: DBConn = Depends(get_neon_connection),
) -> UserRow:
    token = extract_bearer(authorization)
    claims = await verify_clerk_jwt(token)

    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="token missing sub claim"
        )
    clerk_user_id: str = sub

    raw_email = claims.get("email") or claims.get("primary_email_address")
    email: str | None = raw_email if isinstance(raw_email, str) else None

    row = await db.fetchrow(
        """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                  preferred_name, name_pronunciation, native_languages, target_language, target_accents, proficiency, tutor_speaking_speed, goals,
                  location_city, timezone,
                  personalization_consent, product_improvement_consent, consent_screen_seen_at
           FROM users
           WHERE clerk_user_id = $1""",
        clerk_user_id,
    )
    if row is None:
        row = await db.fetchrow(
            """INSERT INTO users (id, clerk_user_id, email)
               VALUES ($1, $2, $3)
               RETURNING id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                         preferred_name, name_pronunciation, native_languages, target_language, target_accents, proficiency, tutor_speaking_speed, goals,
                         location_city, timezone,
                         personalization_consent, product_improvement_consent, consent_screen_seen_at""",
            uuid.uuid4(),
            clerk_user_id,
            email,
        )
        assert row is not None
        return make_user_row(row)

    user = make_user_row(row)
    if email and user["email"] != email:
        await db.execute(
            "UPDATE users SET email = $2, updated_at = NOW() WHERE id = $1",
            user["id"],
            email,
        )
        user["email"] = email
    return user
