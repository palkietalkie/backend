"""CEFR vocab index loaded once at module import. Read-only after load.

Replaces the old cefr_vocab / cefr_frequency DB tables: same data, no seed step, no JOINs.
"""

import csv
from pathlib import Path

from app.services.cefr_vocab.cefr_entry import CefrEntry
from app.services.cefr_vocab.constants import LEVELS

_CSV = Path(__file__).resolve().parents[2] / "scripts" / "data" / "cefr_vocab.csv"


def _load() -> tuple[
    dict[str, CefrEntry],
    dict[str, list[tuple[str, int]]],
    list[tuple[str, CefrEntry]],
]:
    by_lemma: dict[str, CefrEntry] = {}
    by_level: dict[str, list[tuple[str, int]]] = {lvl: [] for lvl in LEVELS}
    with _CSV.open(newline="") as f:
        for row in csv.DictReader(f):
            level = row["cefr"]
            rank = int(row["rank"])
            entry = CefrEntry(level=level, rank=rank)
            by_lemma[row["headword"]] = entry
            by_level.setdefault(level, []).append((row["headword"], rank))
    for level_list in by_level.values():
        level_list.sort(key=lambda x: x[1])
    sorted_by_rank = sorted(by_lemma.items(), key=lambda kv: kv[1].rank)
    return by_lemma, by_level, sorted_by_rank


BY_LEMMA, BY_LEVEL, SORTED_BY_RANK = _load()
