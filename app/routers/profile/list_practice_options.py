"""GET /profile/practice-options — the practice-enum catalog.

Backend owns the Literal types (`Proficiency`, `TutorSpeakingSpeed`) because it has to validate inbound PATCH values and map each slug to a prompt-hint sentence at conversation start. iOS just renders pickers, so it fetches the slug list here instead of duplicating the enum and risking drift when we add or rename a value.

Display labels are not returned — iOS derives them from the slug (snake_case → "Title case") and looks the result up in `Localizable.xcstrings` so the picker stays locale-aware.
"""

from typing import get_args

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.profile.goal import Goal
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


class PracticeOptionsOut(BaseModel):
    proficiency: list[Proficiency]
    tutor_speaking_speed: list[TutorSpeakingSpeed]
    goals: list[Goal]


@router.get("/practice-options", response_model=PracticeOptionsOut)
async def list_practice_options(
    _user: UserRow = Depends(resolve_current_user),
) -> PracticeOptionsOut:
    return PracticeOptionsOut(
        proficiency=list(get_args(Proficiency)),
        tutor_speaking_speed=list(get_args(TutorSpeakingSpeed)),
        goals=list(get_args(Goal)),
    )
