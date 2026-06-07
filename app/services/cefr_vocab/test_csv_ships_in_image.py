"""Guard against the Dockerfile-copy bug that crash-looped Fly dev on 2026-06-05.

The bug: `_CSV` resolved to `backend/scripts/data/cefr_data.csv`, which existed locally so unit tests passed. The Dockerfile only COPYs `app/` and `migrations/`, so the file never reached the image, and uvicorn died at import on first boot. Locking the CSV inside `app/` here catches the next attempt to move it outside the shipped tree before it hits prod.
"""

from pathlib import Path

from app.services.cefr_vocab._data import _CSV


def test_vocab_csv_lives_under_app_tree() -> None:
    app_dir = Path(__file__).resolve().parents[2]
    assert app_dir.name == "app"
    assert _CSV.is_relative_to(app_dir), (
        f"data.csv at {_CSV} must live under {app_dir}/ so the Dockerfile's `COPY app ./app` "
        "ships it. Files outside app/ are not in the image and crash uvicorn at module import."
    )


def test_vocab_csv_exists() -> None:
    assert _CSV.is_file(), (
        f"data.csv missing at {_CSV} — regenerate via scripts/regenerate_cefr_vocab.py"
    )
