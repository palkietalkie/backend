import logging
from datetime import UTC, datetime, time, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)


def _resolve_tz(tz_name: str | None) -> tzinfo:
    if not tz_name:
        return UTC
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # A free-plan day/week window must never 500 the conversation over a timezone string. A valid-but-unresolvable key (e.g. the legacy alias "US/Pacific" on a runtime whose tz database lacks the backward-compat links) degrades to UTC — the window is then off by the local offset, a minor billing-window inaccuracy, not a dead session. The tzdata dependency keeps this rare; this guard is the backstop.
        logger.warning("unresolvable timezone %r, falling back to UTC", tz_name)
        return UTC


def compute_local_day_window(tz_name: str | None) -> tuple[datetime, datetime]:
    # [start_of_local_day, end_of_local_day) as UTC-aware datetimes.
    tz = _resolve_tz(tz_name)
    now_local = datetime.now(tz)
    start_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
