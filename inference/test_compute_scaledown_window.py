from inference.compute_scaledown_window import compute_scaledown_window


def test_scaledown_window_prd_keeps_warm_pool() -> None:
    assert compute_scaledown_window("main") == 120


def test_scaledown_window_non_prd_runs_at_modal_floor() -> None:
    assert compute_scaledown_window("dev") == 2
    assert compute_scaledown_window(None) == 2
    assert compute_scaledown_window("staging") == 2
