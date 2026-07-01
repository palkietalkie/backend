"""Explicit asyncpg.Record → TypedDict constructors.

asyncpg.Record acts like a Mapping[str, Any] so `dict(row)` is `dict[str, Any]`, which is NOT assignable to a TypedDict under pyright strict (the TypedDict requires its literal structural shape, not a generic mapping). These helpers do field-by-field construction, keeping the call sites short while staying fully typed.

The generator (`scripts/generate_neon_types.py`) is the source of truth for the column list — if it drifts from this file, the pre-commit re-run will catch it.
"""

from typing import Any

import asyncpg

from app.services.neon.rows import (
    CalendarTokenRow,
    PersonaRow,
    UserRow,
)


def make_user_row(row: asyncpg.Record) -> UserRow:
    return UserRow(
        id=row["id"],
        clerk_user_id=row["clerk_user_id"],
        email=row["email"],
        premium=row["premium"],
        premium_ends_at=row["premium_ends_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        preferred_name=row["preferred_name"],
        name_pronunciation=row["name_pronunciation"],
        native_languages=list(row["native_languages"]),
        target_language=row["target_language"],
        target_accents=list(row["target_accents"]),
        proficiency=row["proficiency"],
        tutor_speaking_speed=row["tutor_speaking_speed"],
        correction_frequency=row["correction_frequency"],
        goals=row["goals"],
        location_city=row["location_city"],
        timezone=row["timezone"],
        personalization_consent=row["personalization_consent"],
        product_improvement_consent=row["product_improvement_consent"],
        consent_screen_seen_at=row["consent_screen_seen_at"],
        # .get, not [...]: only the auth path SELECTs deleted_at (it gates soft-deleted users); other callers' SELECTs omit it and don't read it, so default None keeps them working without each needing the column.
        deleted_at=row.get("deleted_at"),
    )


def make_persona_row(row: asyncpg.Record) -> PersonaRow:
    return PersonaRow(
        id=row["id"],
        name=row["name"],
        voice_id=row["voice_id"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        description=row["description"],
        role=row["role"],
        vocabulary_register=row["vocabulary_register"],
        conversational_style=row["conversational_style"],
        topical_preferences=row["topical_preferences"],
        is_public=row["is_public"],
        like_count=row["like_count"],
        age=row["age"],
        background=row["background"],
    )


def make_calendar_token_row(row: asyncpg.Record) -> CalendarTokenRow:
    return CalendarTokenRow(
        id=row["id"],
        user_id=row["user_id"],
        provider=row["provider"],
        access_token=row["access_token"],
        refresh_token=row["refresh_token"],
        expires_at=row["expires_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def make_dict(row: asyncpg.Record) -> dict[str, Any]:
    """Generic Record → dict[str, Any] for callers that need flat dict access (e.g. JSON-serialize all columns)."""
    return {k: row[k] for k in row}
