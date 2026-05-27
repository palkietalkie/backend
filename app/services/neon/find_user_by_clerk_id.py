from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def find_user_by_clerk_id(db: DBConn, clerk_user_id: str) -> UserRow | None:
    row = await db.fetchrow(
        """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                  display_name, name_pronunciation,
                  native_language, target_accent, goals,
                  location_city, timezone,
                  personalization_consent, product_improvement_consent, consent_screen_seen_at
           FROM users
           WHERE clerk_user_id = $1""",
        clerk_user_id,
    )
    return dict(row) if row is not None else None  # type: ignore[return-value]
