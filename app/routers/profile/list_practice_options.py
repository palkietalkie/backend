"""GET /profile/practice-options — the practice-enum catalog.

Backend owns the Literal types (`Proficiency`, `TutorSpeakingSpeed`) because it has to validate inbound PATCH values and map each slug to a prompt-hint sentence at conversation start. iOS just renders pickers, so it fetches the slug list here instead of duplicating the enum and risking drift when we add or rename a value.

Display labels are not returned — iOS derives them from the slug (snake_case → "Title case") and looks the result up in `Localizable.xcstrings` so the picker stays locale-aware. The one non-label value returned is the speed playback-rate map, so the picker can show the concrete multiplier ("Slow · 0.85×") sourced from the backend instead of iOS hardcoding numbers that would drift from the real audio.output.speed.
"""

from typing import get_args

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.profile.goal import Goal
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TUTOR_SPEED_PLAYBACK_RATE, TutorSpeakingSpeed
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


class PracticeOptionsOut(BaseModel):
    proficiency: list[Proficiency]
    tutor_speaking_speed: list[TutorSpeakingSpeed]
    # slug → the real audio.output.speed multiplier applied at that level. Additive (build 28 ignores it); lets iOS render the concrete number without owning it. Same map the mint uses, so the UI can never drift from what the audio actually does.
    tutor_speaking_speed_rates: dict[TutorSpeakingSpeed, float]
    goals: list[Goal]


@router.get("/practice-options", response_model=PracticeOptionsOut)
async def list_practice_options(
    _user: UserRow = Depends(resolve_current_user),
) -> PracticeOptionsOut:
    return PracticeOptionsOut(
        proficiency=list(get_args(Proficiency)),
        tutor_speaking_speed=list(get_args(TutorSpeakingSpeed)),
        tutor_speaking_speed_rates=TUTOR_SPEED_PLAYBACK_RATE,
        goals=list(get_args(Goal)),
    )
