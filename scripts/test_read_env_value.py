from pathlib import Path

import pytest

import scripts.read_env_value as mod
from scripts.read_env_value import read_env_value


def test_prefers_shell_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PT_TEST_KEY", "from_shell")
    assert read_env_value("PT_TEST_KEY") == "from_shell"


def test_falls_back_to_dotenv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PT_TEST_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('OTHER=x\nPT_TEST_KEY="from_dotenv"\n')
    monkeypatch.setattr(mod, "_ENV_PATH", env_file)
    assert read_env_value("PT_TEST_KEY") == "from_dotenv"


def test_returns_none_when_absent_everywhere(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("PT_TEST_KEY", raising=False)
    monkeypatch.setattr(mod, "_ENV_PATH", tmp_path / "nope.env")
    assert read_env_value("PT_TEST_KEY") is None
