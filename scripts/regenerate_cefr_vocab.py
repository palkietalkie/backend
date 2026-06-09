#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["wordfreq>=3.1.1"]
# ///
"""Rebuild `app/services/cefr_vocab/data.csv` from wordfreq.

Run only when wordfreq updates its underlying corpora (rare — every 6-12 months) or when we want to change the Zipf → CEFR thresholds:

    uv run scripts/regenerate_cefr_vocab.py

PEP 723 inline metadata above tells uv to install wordfreq into a one-shot venv; the runtime backend never imports wordfreq."""

import csv
import re
from pathlib import Path

from wordfreq import top_n_list, zipf_frequency

_OUT = Path(__file__).resolve().parents[1] / "app" / "services" / "cefr_vocab" / "data.csv"
_TOP_N = 100000
_LEMMA_RE = re.compile(r"^[a-z][a-z'\-]{0,62}[a-z]?$")


def _level(zipf: float) -> str:
    if zipf >= 6.0:
        return "A1"
    if zipf >= 5.0:
        return "A2"
    if zipf >= 4.0:
        return "B1"
    if zipf >= 3.5:
        return "B2"
    if zipf >= 3.0:
        return "C1"
    return "C2"


def main() -> None:
    seen: set[str] = set()
    rows: list[tuple[str, str, int]] = []
    for rank, word in enumerate(top_n_list("en", _TOP_N), start=1):
        lemma = word.strip().lower()
        if " " in lemma or not _LEMMA_RE.match(lemma) or lemma in seen:
            continue
        seen.add(lemma)
        rows.append((lemma, _level(zipf_frequency(lemma, "en")), rank))
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    with _OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["headword", "cefr", "rank"])
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {_OUT}")


if __name__ == "__main__":
    main()
