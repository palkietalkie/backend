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


def test_journaling_companion_present() -> None:
    # The journaling-companion persona (the wedge for low-pressure speaking practice) must ship with its sounding-board role.
    matches = [p for p in PRESETS if p.name == "Journaling companion"]
    assert len(matches) == 1
    assert "sounding board" in matches[0].role.lower()
    assert matches[0].description.strip()


def test_journaling_is_default_and_generic_personas_disabled() -> None:
    # Wes: the default persona is the Journaling companion (lowest sort_weight = first in Recommended = what a new user lands on), and the generic "A man" / "A woman" personas are disabled for now.
    names = [p.name for p in PRESETS]
    assert "A man" not in names
    assert "A woman" not in names
    sort_weight_zero = [p.name for p in PRESETS if p.sort_weight == 0]
    assert sort_weight_zero == ["Journaling companion"]


def test_no_raw_warmth_in_prompt_fed_persona_fields() -> None:
    # De-warming: a bare "warm" instruction in a prompt-fed field tilts the persona sycophantic (against the product vision).
    # Warmth is only allowed paired with a sharpening counterweight (e.g. "kind but no fluff"), never standalone.
    for p in PRESETS:
        for field in (p.role, p.conversational_style, p.vocabulary_register):
            assert "warm" not in field.lower(), f"{p.name!r} has raw warmth in a prompt-fed field"
