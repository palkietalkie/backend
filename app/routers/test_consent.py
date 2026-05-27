"""Consent router tests."""


async def test_consent_starts_unset(app_with_overrides) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/consent")
    assert resp.status_code == 200
    body = resp.json()
    assert body["set"] is False
    assert body["personalization"] is False
    assert body["product_improvement"] is False


async def test_set_consent(app_with_overrides) -> None:
    client, _ = app_with_overrides
    resp = await client.put(
        "/consent",
        json={"personalization": True, "product_improvement": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["set"] is True
    assert body["personalization"] is True
    assert body["product_improvement"] is False

    resp = await client.get("/consent")
    body = resp.json()
    assert body["set"] is True
    assert body["personalization"] is True
