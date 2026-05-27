"""Google Calendar event → CalendarEvent parser tests."""

from typing import Any

from app.services.google_calendar.parse_event import parse_event


def test_parse_event_full_datetime_window() -> None:
    item: dict[str, Any] = {
        "summary": "1:1 with manager",
        "start": {"dateTime": "2026-05-26T09:00:00-07:00"},
        "end": {"dateTime": "2026-05-26T09:30:00-07:00"},
        "location": "Hub-3",
    }
    event = parse_event(item)
    assert event is not None
    assert event.title == "1:1 with manager"
    assert event.location == "Hub-3"
    assert event.start.hour == 9
    assert event.end is not None
    assert event.end.hour == 9


def test_parse_event_all_day_uses_date() -> None:
    item: dict[str, Any] = {
        "summary": "Conference",
        "start": {"date": "2026-05-26"},
        "end": {"date": "2026-05-27"},
    }
    event = parse_event(item)
    assert event is not None
    assert event.start.year == 2026
    assert event.end is not None


def test_parse_event_zulu_time_normalizes_to_utc() -> None:
    item: dict[str, Any] = {
        "summary": "Standup",
        "start": {"dateTime": "2026-05-26T16:00:00Z"},
        "end": {"dateTime": "2026-05-26T16:15:00Z"},
    }
    event = parse_event(item)
    assert event is not None
    assert event.start.tzinfo is not None


def test_parse_event_drops_when_start_missing() -> None:
    assert parse_event({"summary": "no start"}) is None


def test_parse_event_drops_when_neither_datetime_nor_date() -> None:
    assert parse_event({"summary": "x", "start": {}}) is None


def test_parse_event_drops_on_unparseable_iso() -> None:
    item: dict[str, Any] = {
        "summary": "garbage",
        "start": {"dateTime": "not-a-date"},
    }
    assert parse_event(item) is None


def test_parse_event_defaults_title_when_summary_missing() -> None:
    item: dict[str, Any] = {
        "start": {"dateTime": "2026-05-26T10:00:00Z"},
    }
    event = parse_event(item)
    assert event is not None
    assert event.title == "(no title)"


def test_parse_event_handles_missing_end() -> None:
    item: dict[str, Any] = {
        "summary": "open-ended",
        "start": {"dateTime": "2026-05-26T10:00:00Z"},
    }
    event = parse_event(item)
    assert event is not None
    assert event.end is None
