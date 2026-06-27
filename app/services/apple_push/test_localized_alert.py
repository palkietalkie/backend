from app.services.apple_push.localized_alert import LocalizedAlert


def test_body_args_defaults_to_empty_tuple() -> None:
    # Frozen record with an immutable default, no shared-mutable-default trap.
    alert = LocalizedAlert(title_loc_key="t", body_loc_key="b")
    assert alert.body_args == ()


def test_carries_keys_and_args() -> None:
    alert = LocalizedAlert(title_loc_key="title_k", body_loc_key="body_k", body_args=("5",))
    assert (alert.title_loc_key, alert.body_loc_key, alert.body_args) == (
        "title_k",
        "body_k",
        ("5",),
    )
