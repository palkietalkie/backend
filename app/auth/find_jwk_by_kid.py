"""Find the JWK in a JWKS document that matches a given kid, or None if absent."""

from app.auth.jwk import JWK, JWKS


def find_jwk_by_kid(jwks: JWKS, kid: str) -> JWK | None:
    # Returns None (not raise) so the caller can refetch the JWKS on a miss — a miss usually means Clerk rotated keys and our cached set is stale, not that the token is bad.
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return key
    return None
