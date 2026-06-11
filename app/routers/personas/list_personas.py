import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.auth.resolve_current_user import resolve_current_user
from app.personas.presets.preset_list import PRESETS
from app.routers.personas.build_persona_out_from_preset import (
    PersonaOut,
    build_persona_out_from_preset,
)
from app.routers.personas.build_persona_out_from_row import build_persona_out_from_row
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.make_rows import make_persona_row
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])

LIKED_BY_USER_SQL = "SELECT persona_id FROM persona_likes WHERE user_id = $1"

SortOrder = Literal["popular", "recent", "recommended"]


@router.get("", response_model=list[PersonaOut])
async def list_personas(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
    q_param: str | None = Query(
        default=None, alias="q", description="Search term — matches name + description."
    ),
    sort: SortOrder = Query(default="recommended"),
) -> list[PersonaOut]:
    db_rows = await db.fetch(
        """SELECT id, name, description, voice_id, role, age, background,
                  vocabulary_register, conversational_style, topical_preferences,
                  is_public, like_count, user_id, created_at, updated_at
           FROM personas
           WHERE user_id = $1 OR is_public = TRUE""",
        user["id"],
    )
    db_personas = [make_persona_row(row) for row in db_rows]

    preset_like_counts: dict[uuid.UUID, int] = {}
    if PRESETS:
        rows = await db.fetch(
            """SELECT persona_id, COUNT(id)::int AS like_count
               FROM persona_likes
               WHERE persona_id = ANY($1::uuid[])
               GROUP BY persona_id""",
            [p.id for p in PRESETS],
        )
        preset_like_counts = {row["persona_id"]: int(row["like_count"]) for row in rows}

    liked_rows = await db.fetch(LIKED_BY_USER_SQL, user["id"])
    liked_ids: set[uuid.UUID] = {row["persona_id"] for row in liked_rows}

    items: list[PersonaOut] = [
        build_persona_out_from_preset(p, liked_ids=liked_ids, like_counts=preset_like_counts)
        for p in PRESETS
    ]
    items += [
        build_persona_out_from_row(p, user_id=user["id"], liked_ids=liked_ids) for p in db_personas
    ]

    if q_param:
        needle = q_param.lower()
        items = [
            i
            for i in items
            if needle in i.name.lower()
            or needle in i.description.lower()
            or (i.role and needle in i.role.lower())
            or (i.topical_preferences and needle in i.topical_preferences.lower())
        ]

    if sort == "popular":
        items.sort(key=lambda i: (-i.like_count, i.name.lower()))
    elif sort == "recent":
        items.sort(key=lambda i: (i.is_preset, i.name.lower()))
    else:
        items.sort(
            key=lambda i: (
                not i.is_owner,
                not i.is_preset,
                i.sort_weight,
                -i.like_count,
                i.name.lower(),
            )
        )
    return items
