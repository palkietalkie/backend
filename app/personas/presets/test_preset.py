"""Tests Preset dataclass + its derived id + voice picker."""

import uuid

from app.personas.presets.compute_preset_id import compute_preset_id
from app.personas.presets.preset import Preset


def _make(name: str = "Test") -> Preset:
    return Preset(
        name=name,
        description="d",
        role="r",
        age="a",
        background="b",
        vocabulary_register="v",
        conversational_style="c",
        topical_preferences="t",
    )


def test_preset_id_is_stable_uuid_derived_from_name() -> None:
    p = _make("Stable Tester")
    assert p.id == compute_preset_id("Stable Tester")
    assert isinstance(p.id, uuid.UUID)


def test_preset_id_differs_for_different_names() -> None:
    assert _make("A").id != _make("B").id


def test_preset_is_frozen() -> None:
    p = _make()
    try:
        p.name = "Other"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Preset should be frozen")


def test_voice_for_returns_id_from_provider_catalog() -> None:
    p = _make()
    vid = p.voice_for("openai")
    assert isinstance(vid, str) and vid


def test_default_sort_weight() -> None:
    assert _make().sort_weight == 100
