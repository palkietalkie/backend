from app.services.apple_push.localized_alert import LocalizedAlert

_TITLE = "notif_weekly_recap_title"


def build_weekly_recap_alert(sessions: int, minutes: int, streak: int) -> LocalizedAlert:
    """The weekly recap push (#6): "N sessions, M min this week" + a streak call-to-action.

    Every count is a numeral arg (so "1 session" stays consistent with "1 min", never a spelled-out "One"). The _one vs _other key only swaps the singular/plural NOUN, which is the one thing on-device plural rules can't do for string loc-args. Minutes uses the invariant "min" abbreviation and the streak clause is phrased plural-safely per locale, so neither needs its own form.

    `streak` is the CURRENT live streak (compute_day_streak at send time), NOT a weekly figure, so the clause states it as present state ("you're on an N-day streak"), which is honest even when it diverges from the week (a Mon-Fri run rested over the weekend reads 0 here). Streak 0 (lapsed) drops the clause. Caller guarantees sessions >= 1 and minutes >= 1 (floored)."""
    singular = sessions == 1
    if streak > 0:
        key = "notif_weekly_recap_body_one" if singular else "notif_weekly_recap_body_other"
        return LocalizedAlert(_TITLE, key, (str(sessions), str(minutes), str(streak)))
    key = (
        "notif_weekly_recap_body_one_no_streak"
        if singular
        else "notif_weekly_recap_body_other_no_streak"
    )
    return LocalizedAlert(_TITLE, key, (str(sessions), str(minutes)))
