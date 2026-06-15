import pytest

from app.services.neo4j.is_self_reference import is_self_reference


@pytest.mark.parametrize(
    "name", ["__SELF__", "__self__", "user", "User", "the user", "me", "I", "  Myself "]
)
def test_self_aliases_are_recognized(name: str) -> None:
    assert is_self_reference(name) is True


@pytest.mark.parametrize("name", ["Joe Pau", "Tennis", "userland", "mes", "Canada", ""])
def test_real_entities_are_not_self(name: str) -> None:
    assert is_self_reference(name) is False


@pytest.mark.parametrize("name", ["Wes", "  wes ", "WES"])
def test_users_own_name_resolves_to_self_when_supplied(name: str) -> None:
    assert is_self_reference(name, user_name="Wes") is True


def test_users_own_name_does_not_leak_without_supplying_it() -> None:
    # "Wes" is only self when we know it's the user's name; otherwise it's a normal entity (could be a friend).
    assert is_self_reference("Wes") is False
