"""Find the JWK in a JWKS document that matches a given kid."""

from fastapi import HTTPException, status

from app.auth.jwk import JWK, JWKS


def find_jwk_by_kid(jwks: JWKS, kid: str) -> JWK:
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown kid in token header"
    )
