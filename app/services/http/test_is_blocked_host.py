import pytest

from app.services.http.is_blocked_host import is_blocked_host


@pytest.mark.parametrize(
    "host", ["localhost", "127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.1.1", ""]
)
def test_blocks_internal_hosts(host: str) -> None:
    assert is_blocked_host(host) is True


@pytest.mark.parametrize("host", ["example.com", "8.8.8.8", "api.openai.com"])
def test_allows_public_hosts(host: str) -> None:
    assert is_blocked_host(host) is False
