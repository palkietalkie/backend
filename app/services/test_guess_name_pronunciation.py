"""Calls Gemma to produce a CAPITAL-SYLLABLES hint; we mock the LLM and verify framing + edge cases."""

import pytest

from app.services import guess_name_pronunciation as mod
from app.services.guess_name_pronunciation import guess_name_pronunciation


@pytest.fixture
def stub_gemma(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Captures every (prompt, system) Gemma would have been called with, returns a deterministic answer."""
    calls: list[dict[str, str]] = []

    async def _fake_complete_text(*, prompt: str, system: str) -> str:
        calls.append({"prompt": prompt, "system": system})
        return "  AH-YOO-mee  "  # extra whitespace to confirm we strip

    monkeypatch.setattr(mod, "complete_text", _fake_complete_text)
    return calls


async def test_returns_stripped_llm_output(stub_gemma: list[dict[str, str]]) -> None:
    result = await guess_name_pronunciation("Ayumi", "English")
    assert result == "AH-YOO-mee"
    assert len(stub_gemma) == 1


async def test_empty_preferred_name_short_circuits_without_calling_gemma(
    stub_gemma: list[dict[str, str]],
) -> None:
    assert await guess_name_pronunciation("", "English") == ""
    assert stub_gemma == []


async def test_whitespace_only_preferred_name_short_circuits_without_calling_gemma(
    stub_gemma: list[dict[str, str]],
) -> None:
    assert await guess_name_pronunciation("    ", "English") == ""
    assert stub_gemma == []


async def test_target_language_threads_into_system_prompt(
    stub_gemma: list[dict[str, str]],
) -> None:
    await guess_name_pronunciation("Joaquín", "Spanish")
    assert "Spanish" in stub_gemma[0]["system"]
    assert "Joaquín" in stub_gemma[0]["prompt"]
    assert "Spanish" in stub_gemma[0]["prompt"]


async def test_user_prompt_does_not_carry_extra_quoting(stub_gemma: list[dict[str, str]]) -> None:
    await guess_name_pronunciation("Niamh", "English")
    assert stub_gemma[0]["prompt"].startswith("Name: Niamh")
