from app.services.openai.compute_realtime_cost import compute_realtime_cost


def test_computes_cost_from_tokens_and_model_rate() -> None:
    # gpt-realtime-2 = $32/M input, $64/M output. 120k input -> $3.84, 45k output -> $2.88.
    cost = compute_realtime_cost("gpt-realtime-2", 120_000, 45_000)
    assert cost is not None
    input_cost, output_cost = cost
    assert round(input_cost, 6) == 3.84
    assert round(output_cost, 6) == 2.88


def test_mini_rate_is_cheaper() -> None:
    cost = compute_realtime_cost("gpt-realtime-mini", 1_000_000, 1_000_000)
    assert cost == (10.0, 20.0)


def test_none_when_no_tokens() -> None:
    # PersonaPlex / a session that never reported usage: no cost, not a wrong 0.
    assert compute_realtime_cost("gpt-realtime-2", None, None) is None
    assert compute_realtime_cost("gpt-realtime-2", 100, None) is None


def test_none_for_unknown_model() -> None:
    assert compute_realtime_cost("personaplex-7b", 100, 100) is None
    assert compute_realtime_cost(None, 100, 100) is None
