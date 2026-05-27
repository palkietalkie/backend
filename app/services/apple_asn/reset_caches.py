from app.services.apple_asn import _state


def reset_caches() -> None:
    _state.ROOT_CERTS_CACHE = None
    _state.VERIFIER_CACHE = None
