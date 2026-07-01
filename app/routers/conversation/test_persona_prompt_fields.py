import dataclasses

from app.routers.conversation.persona_prompt_fields import PersonaPromptFields


def test_is_frozen_so_prompt_fields_cant_mutate_mid_assembly() -> None:
    # Introspect rather than attempt an assignment: a direct `fields.name = ...` is a static type error pyright rejects, and the point is just that the record is frozen.
    assert dataclasses.is_dataclass(PersonaPromptFields)
    params = getattr(PersonaPromptFields, "__dataclass_params__")  # noqa: B009 — dunder not a normal attribute
    assert params.frozen
