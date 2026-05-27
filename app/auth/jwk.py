"""JWK + JWKS type shapes per RFC 7517."""

from typing import TypedDict


class JWK(TypedDict, total=False):
    # Field set varies by algorithm: RSA uses n/e, EC uses x/y/crv. All are str regardless.
    kty: str
    kid: str
    use: str
    alg: str
    n: str
    e: str
    x: str
    y: str
    crv: str


class JWKS(TypedDict):
    keys: list[JWK]
