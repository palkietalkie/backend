import uuid

from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.services.neon.db_conn import DBConn


async def resolve_persona_names(db: DBConn, persona_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Map persona ids to display names: presets resolve in-code, user-created ones from the personas table."""
    names: dict[uuid.UUID, str] = {}
    db_unknown: list[uuid.UUID] = []
    for persona_id in persona_ids:
        preset = find_preset_by_id(persona_id)
        if preset is not None:
            names[persona_id] = preset.name
        else:
            db_unknown.append(persona_id)
    if db_unknown:
        rows = await db.fetch("SELECT id, name FROM personas WHERE id = ANY($1)", db_unknown)
        for row in rows:
            names[row["id"]] = row["name"]
    return names
