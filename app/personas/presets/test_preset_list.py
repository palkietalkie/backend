"""Lock invariants on the curated preset catalog: every name is unique, every id is unique, every required field is non-empty."""

from app.personas.presets.preset_list import PRESETS


def test_preset_names_are_unique() -> None:
    names = [p.name for p in PRESETS]
    assert len(names) == len(set(names)), f"duplicate preset names: {names}"


def test_preset_ids_are_unique() -> None:
    ids = [p.id for p in PRESETS]
    assert len(ids) == len(set(ids))


def test_every_preset_has_required_fields_non_empty() -> None:
    for p in PRESETS:
        for field in (
            "name",
            "description",
            "role",
            "age",
            "background",
            "vocabulary_register",
            "conversational_style",
            "topical_preferences",
        ):
            assert getattr(p, field).strip(), f"preset {p.name!r} has empty {field!r}"


def test_catalog_not_empty() -> None:
    assert len(PRESETS) > 0


def test_preset_descriptions_have_no_em_or_en_dashes() -> None:
    # No em/en dashes in user-facing copy (the board-member description was de-dashed).
    for p in PRESETS:
        assert "—" not in p.description and "–" not in p.description, p.name
