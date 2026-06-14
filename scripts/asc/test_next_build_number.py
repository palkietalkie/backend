"""Lock the build-number rule: clean +1 off the real high-water mark, robust to the old scheme's stragglers."""

from scripts.asc.next_build_number import compute_next_build_number


def test_next_is_one_above_highest():
    # The exact case that prompted the fix: builds [26, 1] → 27, not 2 and not a commit count.
    assert compute_next_build_number(["26", "1"]) == 27


def test_sequential_run():
    assert compute_next_build_number(["1", "2", "3"]) == 4


def test_first_ever_upload_is_one():
    assert compute_next_build_number([]) == 1


def test_ignores_non_integer_build_numbers():
    # Defensive against a stray dotted/None CFBundleVersion from an older scheme.
    assert compute_next_build_number([None, "26", "1.0.3"]) == 27
