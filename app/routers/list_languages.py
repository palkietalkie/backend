"""GET /languages — the supported-languages catalog with their accents.

iOS uses this to populate the native_language / target_language / target_accent pickers without duplicating the 36-language × ~4-accent list client-side. The catalog lives in `app/profile/languages.py` as Literal types + a `LANGUAGES` tuple; this endpoint just exposes it as JSON."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.profile.languages import LANGUAGES, AccentName, LanguageName
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/languages", tags=["languages"])


class LanguageOut(BaseModel):
    name: LanguageName
    accents: list[AccentName]


@router.get("", response_model=list[LanguageOut])
async def list_languages(_user: UserRow = Depends(resolve_current_user)) -> list[LanguageOut]:
    return [LanguageOut(name=lang.name, accents=list(lang.accents)) for lang in LANGUAGES]
