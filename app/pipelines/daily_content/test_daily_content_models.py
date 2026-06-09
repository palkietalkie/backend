"""Tests for the TalkItem dataclass — flat shape shared across news / quiz topics."""

from dataclasses import FrozenInstanceError

import pytest

from app.pipelines.daily_content.models import TalkItem


def test_talk_item_fields() -> None:
    item = TalkItem(title="t", summary="s", source="src", image_url="https://x.test/a.png")
    assert item.title == "t"
    assert item.summary == "s"
    assert item.source == "src"
    assert item.image_url == "https://x.test/a.png"


def test_talk_item_is_frozen() -> None:
    item = TalkItem(title="t", summary="s", source="", image_url="")
    with pytest.raises(FrozenInstanceError):
        item.title = "x"  # type: ignore[misc]


def test_talk_item_quiz_shape_allows_empty_source_and_image() -> None:
    # Quizzes leave source + image_url empty; news fills both. Flat shape supports either.
    quiz = TalkItem(title="What year?", summary="Pick one.", source="", image_url="")
    assert quiz.source == ""
    assert quiz.image_url == ""
