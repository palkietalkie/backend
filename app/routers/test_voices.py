"""Voice library router tests."""


async def test_list_voices_returns_all_17(app_with_overrides) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/voices")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 17
    ids = {v["id"] for v in body}
    assert "NATM1" in ids
    assert "VARF4" in ids
