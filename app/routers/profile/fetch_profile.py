from fastapi import APIRouter, Depends

from app.auth.resolve_current_user import resolve_current_user
from app.profile.is_language_name import is_language_name
from app.routers.profile.build_profile_out import ProfileOut, build_profile_out
from app.services.guess_name_pronunciation import guess_name_pronunciation
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
async def fetch_profile(
    user: UserRow = Depends(resolve_current_user),
) -> ProfileOut:
    # Compute a placeholder suggestion when stored pronunciation is empty (null OR whitespace-only). The suggestion is returned in a separate field for iOS to display as a TextField placeholder; it is NEVER persisted. User's explicit clears are respected — they keep seeing a fresh suggestion every visit but the stored value stays empty until they actively type and save.
    stored_pronunciation = (user["name_pronunciation"] or "").strip()
    target_language = user["target_language"]
    suggestion: str | None = None
    if user["preferred_name"] and not stored_pronunciation and is_language_name(target_language):
        guessed = await guess_name_pronunciation(user["preferred_name"], target_language)
        if guessed.strip():
            suggestion = guessed.strip()
    return build_profile_out(user, name_pronunciation_suggestion=suggestion)
