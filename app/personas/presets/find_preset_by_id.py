import uuid

from app.personas.presets.preset import Preset
from app.personas.presets.preset_list import PRESETS

_BY_ID: dict[uuid.UUID, Preset] = {p.id: p for p in PRESETS}


def find_preset_by_id(persona_id: uuid.UUID) -> Preset | None:
    return _BY_ID.get(persona_id)
