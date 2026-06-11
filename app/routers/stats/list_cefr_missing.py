from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.cefr_vocab.find_missing import find_missing
from app.services.cefr_vocab.find_missing_by_level import find_missing_by_level
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.list_user_lemmas import list_user_lemmas
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/stats", tags=["stats"])


class MissingWord(BaseModel):
    lemma: str
    level: str


@router.get("/cefr", response_model=list[MissingWord])
async def list_cefr_missing(
    level: str | None = Query(default=None, pattern="^(A1|A2|B1|B2|C1|C2)$"),
    limit: int = Query(default=100, ge=1, le=500),
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> list[MissingWord]:
    used_lemmas = await list_user_lemmas(db, user["id"])
    pairs = (
        find_missing_by_level(used_lemmas, level, limit)
        if level is not None
        else find_missing(used_lemmas, limit)
    )
    return [MissingWord(lemma=lemma, level=lvl) for lemma, lvl in pairs]
