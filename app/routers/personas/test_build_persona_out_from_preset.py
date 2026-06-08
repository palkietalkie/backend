"""Tests for build_persona_out_from_preset — the preset → PersonaOut adapter."""

import uuid

from app.personas.presets.preset import Preset
from app.routers.personas.build_persona_out_from_preset import build_persona_out_from_preset


def _make_preset(name: str = "Tester", sort_weight: int = 100) -> Preset:
    return Preset(
        name=name,
        description="d",
        role="r",
        age="40s",
        background="b",
        vocabulary_register="v",
        conversational_style="c",
        topical_preferences="t",
        sort_weight=sort_weight,
    )


def test_marks_preset_public_and_not_owned() -> None:
    p = _make_preset()
    out = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert out.is_preset is True
    assert out.is_public is True
    assert out.is_owner is False


def test_propagates_character_fields_verbatim() -> None:
    p = _make_preset()
    out = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert out.name == p.name
    assert out.description == p.description
    assert out.role == p.role
    assert out.age == p.age
    assert out.background == p.background
    assert out.vocabulary_register == p.vocabulary_register
    assert out.conversational_style == p.conversational_style
    assert out.topical_preferences == p.topical_preferences


def test_like_count_reads_from_dict_with_zero_default() -> None:
    p = _make_preset()
    out_zero = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert out_zero.like_count == 0
    out_some = build_persona_out_from_preset(p, liked_ids=set(), like_counts={p.id: 7})
    assert out_some.like_count == 7


def test_liked_by_me_reads_from_set() -> None:
    p = _make_preset()
    out_unliked = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert out_unliked.liked_by_me is False
    out_liked = build_persona_out_from_preset(p, liked_ids={p.id}, like_counts={})
    assert out_liked.liked_by_me is True


def test_sort_weight_round_trips_into_output() -> None:
    out = build_persona_out_from_preset(
        _make_preset(sort_weight=0), liked_ids=set(), like_counts={}
    )
    assert out.sort_weight == 0


def test_id_matches_preset_id_uuid() -> None:
    p = _make_preset()
    out = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert isinstance(out.id, uuid.UUID)
    assert out.id == p.id


def test_voice_id_picked_from_provider_catalog() -> None:
    p = _make_preset()
    out = build_persona_out_from_preset(p, liked_ids=set(), like_counts={})
    assert isinstance(out.voice_id, str) and out.voice_id
