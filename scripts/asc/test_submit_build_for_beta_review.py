"""select_build is the only non-network logic; lock its two rules: never offer a non-VALID build, and default to the newest VALID."""

import pytest

from scripts.asc.submit_build_for_beta_review import select_build

_BUILDS = [
    {"id": "b27", "attributes": {"version": "27", "processingState": "PROCESSING"}},
    {"id": "b26", "attributes": {"version": "26", "processingState": "VALID"}},
    {"id": "b25", "attributes": {"version": "25", "processingState": "VALID"}},
]


def test_defaults_to_newest_valid_skipping_unprocessed():
    # 27 is still PROCESSING — must not be picked even though it's newest.
    assert select_build(_BUILDS, None)["id"] == "b26"


def test_selects_requested_version():
    assert select_build(_BUILDS, "25")["id"] == "b25"


def test_requested_version_must_be_valid():
    with pytest.raises(SystemExit):
        select_build(_BUILDS, "27")


def test_no_valid_build_aborts():
    with pytest.raises(SystemExit):
        select_build(
            [{"id": "x", "attributes": {"version": "9", "processingState": "PROCESSING"}}], None
        )
