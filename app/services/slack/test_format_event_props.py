from app.services.slack.format_event_props import format_event_props


def test_returns_empty_string_for_empty_dict() -> None:
    assert format_event_props({}) == ""


def test_renders_single_pair_as_backticked_key_value() -> None:
    assert format_event_props({"duration_ms": 1234}) == "`duration_ms=1234`"


def test_joins_multiple_pairs_with_spaces_in_insertion_order() -> None:
    out = format_event_props({"a": 1, "b": "two", "c": 3.5})
    assert out == "`a=1` `b=two` `c=3.5`"


def test_passes_non_scalar_values_through_repr() -> None:
    out = format_event_props({"payload": {"nested": True}, "items": [1, 2]})
    assert "`payload={'nested': True}`" in out
    assert "`items=[1, 2]`" in out


def test_does_not_escape_backticks_in_values() -> None:
    # Documents current behavior — if a value contains ``, Slack will render it weirdly. Worth fixing if we ever pass user-controlled strings; today only backend-controlled props flow through.
    out = format_event_props({"path": "`/v1/foo`"})
    assert out == "`path=`/v1/foo``"
