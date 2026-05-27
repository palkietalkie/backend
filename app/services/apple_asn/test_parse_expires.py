from datetime import UTC, datetime

from app.services.apple_asn.parse_expires import parse_expires


def test_parse_expires_from_transaction() -> None:
    now_ms = int(datetime.now(UTC).timestamp() * 1000) + 60_000
    out = parse_expires({"expiresDate": now_ms}, {})
    assert out is not None
    assert out > datetime.now(UTC)


def test_parse_expires_falls_back_to_renewal() -> None:
    now_ms = int(datetime.now(UTC).timestamp() * 1000) + 60_000
    out = parse_expires({}, {"renewalDate": now_ms})
    assert out is not None


def test_parse_expires_returns_none_when_absent() -> None:
    assert parse_expires({}, {}) is None
