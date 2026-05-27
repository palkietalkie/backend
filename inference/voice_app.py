"""Modal app entry for the `voice` app.

`modal deploy inference/voice_app.py` deploys all decorated functions in this package. The
sibling modules (``download_weights.py``, ``voice.py``, ``warm_voice.py``) are imported below so
their ``@app.X`` decorators register on this ``modal.App`` instance.

App name is `voice` (not `personaplex`) so URLs survive a model swap. URL becomes
``{workspace}--voice-api.modal.run`` (workspace adds `-dev` suffix on the dev environment).
"""

from __future__ import annotations

import os

import modal
from compute_scaledown_window import compute_scaledown_window
from voice_image import image

HF_REPO = "nvidia/personaplex-7b-v1"

app = modal.App("voice")

# boot.sh sets MODAL_ENVIRONMENT=dev. deploy-inference.yml (prd path on push to main) leaves it unset; Modal injects "main" at deploy time. Anything else falls through to the 1s floor.
SCALEDOWN_WINDOW = compute_scaledown_window(os.environ.get("MODAL_ENVIRONMENT"))

# NVMe-backed Volume holding the downloaded Moshi weights. Created lazily on first deploy; subsequent containers mount it read-only and load in ~3-5s.
weights_volume = modal.Volume.from_name("personaplex-weights", create_if_missing=True)

_ = image  # re-exported below so siblings can import a single source of truth
IMAGE = image

# Register sibling decorators on `app` so `modal deploy` discovers them.
from download_weights import download_weights  # noqa: E402, F401
from voice import Voice  # noqa: E402, F401
from warm_voice import warm_voice  # noqa: E402, F401
