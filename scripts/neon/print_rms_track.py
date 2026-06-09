"""Print a per-second RMS strip chart of a mono float audio array."""

from __future__ import annotations

import numpy as np


def print_rms_track(audio: np.ndarray, sr: int) -> None:
    dur = len(audio) / sr
    print("\nPer-second RMS (dBFS, ascii bar — '·' = effectively silent <-50dB):")
    for i in range(int(dur) + 1):
        chunk = audio[i * sr : (i + 1) * sr]
        if len(chunk) < 100:
            continue
        rms = float(np.sqrt((chunk**2).mean()))
        db = 20 * np.log10(rms + 1e-12)
        marker = "·" if db < -50 else " "
        bar = "█" * max(0, int((db + 60) / 2))
        print(f"  t={i:3d}s  {db:7.2f} dB {marker}  {bar}")
