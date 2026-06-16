"""Lock the App Privacy declaration: it's transcribed by hand into the ASC dashboard (no API), so a malformed row would silently ship a wrong privacy label."""

from app.asc.app_privacy import (
    ANALYTICS,
    APP_FUNCTIONALITY,
    APP_PRIVACY,
    OTHER_PURPOSES,
    PRODUCT_PERSONALIZATION,
)

# Apple's six questionnaire purposes; "Third-Party Advertising" and "Developer's Marketing" are deliberately unused (no ads).
_VALID_PURPOSES = {APP_FUNCTIONALITY, ANALYTICS, PRODUCT_PERSONALIZATION, OTHER_PURPOSES}


def test_no_data_used_for_tracking() -> None:
    # The "Nothing is tracked" claim in the module docstring is load-bearing for the label; assert it can't drift.
    assert all(not row.used_for_tracking for row in APP_PRIVACY)


def test_every_row_has_at_least_one_valid_purpose() -> None:
    for row in APP_PRIVACY:
        assert row.purposes, f"{row.category}/{row.data_type} has no purpose"
        assert set(row.purposes) <= _VALID_PURPOSES, f"{row.data_type} has an unknown purpose"


def test_no_duplicate_data_types() -> None:
    keys = [(row.category, row.data_type) for row in APP_PRIVACY]
    assert len(keys) == len(set(keys))


def test_category_and_type_non_empty() -> None:
    for row in APP_PRIVACY:
        assert row.category and row.data_type
