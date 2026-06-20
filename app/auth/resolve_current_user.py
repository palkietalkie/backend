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

    # Load the row, JIT-creating it on first sight. On first sign-in the client fires authenticated requests on independent connections (RootView's GET /consent, and POST /devices/apns dispatched from its own Task in the APNs-token callback) that all miss this not-yet-created row and race to INSERT it; ON CONFLICT DO NOTHING lets one win while the losers write nothing and re-read the winner's row on the next pass, instead of raising UniqueViolationError on ix_users_clerk_user_id (the 500 every brand-new user hit until the row existed). The INSERT guarantees the row exists, so the loop reads it back in at most two passes.
    row = None
    while row is None:
        row = await db.fetchrow(
            """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                      preferred_name, name_pronunciation, native_languages, target_language, target_accents, proficiency, tutor_speaking_speed, goals,
                      location_city, timezone,
                      personalization_consent, product_improvement_consent, consent_screen_seen_at, deleted_at
               FROM users
               WHERE clerk_user_id = $1""",
            clerk_user_id,
        )
        if row is None:
            await db.execute(
                """INSERT INTO users (id, clerk_user_id, email)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (clerk_user_id) DO NOTHING""",
                uuid.uuid4(),
                clerk_user_id,
                email,
            )
    if row["deleted_at"] is not None:
        # Soft-deleted account: the row is retained for counts, but the user is gone — reject every authenticated request so a re-login can't resurrect access.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account deleted")

    user = make_user_row(row)
    if email and user["email"] != email:
        await db.execute(
            "UPDATE users SET email = $2, updated_at = NOW() WHERE id = $1",
            user["id"],
            email,
        )
        user["email"] = email
    return user
