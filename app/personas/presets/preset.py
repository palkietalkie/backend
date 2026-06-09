import random
import uuid
from dataclasses import dataclass

from app.personas.presets.compute_preset_id import compute_preset_id
from app.personas.voices.list_voices_for_provider import list_voices_for_provider


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    role: str
    age: str
    background: str
    vocabulary_register: str
    conversational_style: str
    topical_preferences: str
    # Lower runs first in the Recommended sort. Bare/neutral personas (Tom, Emily) get 0 so they're the default for new users; everything else stays at 100.
    sort_weight: int = 100

    @property
    def id(self) -> uuid.UUID:
        return compute_preset_id(self.name)

    def voice_for(self, provider: str) -> str:
        return random.choice(list_voices_for_provider(provider)).id  # noqa: S311
