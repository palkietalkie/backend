from fastapi import APIRouter, Depends, Response, status

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/account", tags=["account"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> Response:
    # Soft delete only: stamp deleted_at so the account disappears from the user's side (resolve_current_user then rejects them) while the row survives for total-user counts. Idempotent — re-deleting a deleted account is a no-op (it can't even reach here, since the dependency 403s first, but the guard keeps the first stamp stable).
    await db.execute(
        "UPDATE users SET deleted_at = NOW(), updated_at = NOW() WHERE id = $1 AND deleted_at IS NULL",
        user["id"],
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
