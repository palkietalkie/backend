"""PCM silence-detection thresholds, read by moshi/server.py's opus_loop.

Bundled into the Modal container image at /root/inactivity_thresholds.py via voice_image.py so the
runtime imports work too. Module is dep-free so pytest can import it without standing up the full
inference stack.
"""

from __future__ import annotations

PALKIE_INACTIVITY_TIMEOUT_S = 60.0
PALKIE_VOICE_RMS_THRESHOLD = 0.01
