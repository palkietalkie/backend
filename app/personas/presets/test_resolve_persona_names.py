import uuid

from app.personas.presets.preset_list import PRESETS
from app.personas.presets.resolve_persona_names import resolve_persona_names
from app.services.neon.db_conn import DBConn


async def test_resolves_preset_name(db: DBConn) -> None:
    preset = PRESETS[0]
    names = await resolve_persona_names(db, {preset.id})
    assert names[preset.id] == preset.name


async def test_unknown_id_is_absent(db: DBConn) -> None:
    names = await resolve_persona_names(db, {uuid.uuid4()})
    assert names == {}
