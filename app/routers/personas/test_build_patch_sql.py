"""Pure-builder tests for build_patch_sql."""

import uuid
from datetime import UTC, datetime

from app.routers.personas.build_patch_sql import (
    UPDATABLE_FIELDS,
    PersonaUpdate,
    build_patch_sql,
)
from app.services.neon.rows import PersonaRow


def _persona(**overrides: object) -> PersonaRow:
    base: PersonaRow = PersonaRow(
        id=uuid.uuid4(),
        name="x",
        voice_id="NATM1",
        user_id=uuid.uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        description="",
        role=None,
        vocabulary_register=None,
        conversational_style=None,
        topical_preferences=None,
        is_public=False,
        like_count=0,
        age=None,
        background=None,
    )
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


def test_build_patch_sql_empty_body_returns_empty_sql() -> None:
    p = _persona()
    sql, values = build_patch_sql(p, PersonaUpdate())
    assert sql == ""
    assert values == []


def test_build_patch_sql_single_field_uses_one_param_and_appends_id() -> None:
    p = _persona()
    sql, values = build_patch_sql(p, PersonaUpdate(name="new-name"))
    assert values == ["new-name", p["id"]]
    assert "name = $1" in sql
    assert "WHERE id = $2" in sql
    assert "updated_at = NOW()" in sql


def test_build_patch_sql_multiple_fields_in_definition_order() -> None:
    p = _persona()
    body = PersonaUpdate(
        voice_id="ASH",
        name="ren",
        is_public=True,
    )
    sql, values = build_patch_sql(p, body)
    # UPDATABLE_FIELDS order is canonical: name, description, voice_id, ..., is_public last.
    assert values[:-1] == ["ren", "ASH", True]
    assert values[-1] == p["id"]
    assert sql.startswith("UPDATE personas SET")


def test_build_patch_sql_returning_clause_carries_full_row() -> None:
    p = _persona()
    sql, _ = build_patch_sql(p, PersonaUpdate(name="x"))
    # The router relies on the returning clause carrying every column the response model needs.
    for col in (
        "id",
        "name",
        "description",
        "voice_id",
        "role",
        "age",
        "background",
        "vocabulary_register",
        "conversational_style",
        "topical_preferences",
        "is_public",
        "like_count",
        "user_id",
        "created_at",
        "updated_at",
    ):
        assert col in sql


def test_updatable_fields_contains_known_set() -> None:
    # Lock the list — adding a column should also extend the patch surface intentionally.
    assert set(UPDATABLE_FIELDS) == {
        "name",
        "description",
        "voice_id",
        "role",
        "age",
        "background",
        "vocabulary_register",
        "conversational_style",
        "topical_preferences",
        "is_public",
    }
