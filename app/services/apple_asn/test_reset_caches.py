from app.services.apple_asn import _state
from app.services.apple_asn.reset_caches import reset_caches


def test_reset_caches_clears_module_state() -> None:
    _state.VERIFIER_CACHE = object()
    _state.ROOT_CERTS_CACHE = [b"x"]
    reset_caches()
    assert _state.VERIFIER_CACHE is None
    assert _state.ROOT_CERTS_CACHE is None
