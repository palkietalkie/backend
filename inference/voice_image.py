"""Modal image for the `voice` app.

Single responsibility: define the container image that runs PersonaPlex.
The vendored Moshi source lives at `inference/moshi/` and is dropped straight into `/root/moshi/` (importable from the container's CWD). All deps are listed explicitly below — no `pip install` of a local pyproject.toml. Edits to the model server are normal git diffs.
"""

from __future__ import annotations

import modal

WEIGHTS_DIR = "/weights"

# Image: vendored NVIDIA PersonaPlex Moshi fork (NOT upstream kyutai/moshi). The fork's loaders.get_mimi/get_moshi_lm hardcode dep_q=16 and other PersonaPlex-specific kwargs at module-level; upstream Moshi's CheckpointInfo API reads these from a config that PersonaPlex doesn't ship, so we'd crash with KeyError('dep_q'). Dep pins below mirror NVIDIA's pyproject.toml (snapshot recorded in inference/moshi/SOURCE.md).
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "libsndfile1", "libopus-dev")
    .uv_pip_install(
        # PyTorch (NVIDIA's fork pins torch>=2.2,<2.5)
        "torch==2.4.1",
        "torchaudio==2.4.1",
        # Moshi runtime deps (from NVIDIA pyproject.toml)
        "numpy>=1.26,<2.2",
        "safetensors>=0.4.0,<0.5",
        "einops==0.7",
        "sentencepiece==0.2",
        "sounddevice==0.5",
        "sphn>=0.1.4,<0.2",
        # Backend / auth deps
        "huggingface_hub[hf_transfer]==0.24.7",
        "PyJWT[crypto]==2.10.1",
        "cryptography==44.0.0",
        "httpx==0.27.2",
        "aiohttp==3.10.10",
        extra_index_url="https://download.pytorch.org/whl/cu124",
    )
    # Vendored moshi source — dropped into /root/moshi/ so `import moshi` resolves from the container's working directory. Copied from NVIDIA/personaplex@main; see inference/moshi/SOURCE.md.
    .add_local_dir("inference/moshi", remote_path="/root/moshi", copy=True)
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            # Point HF cache at the NVMe-mounted Volume. download_weights populates this path; load_model reads from it via standard HF cache resolution.
            "HF_HOME": WEIGHTS_DIR,
            "HF_HUB_CACHE": WEIGHTS_DIR,
        }
    )
    # Bundle the SRP-split helpers and the canonical HMAC ticket package into /root so the container can import them. voice_app.py (and its decorator-importing siblings voice.py / download_weights.py / warm_voice.py) imports voice_image / ticket_auth_middleware / start_aiohttp_in_thread; without these the WS gets accepted, server sends handshake, then the container dies and iOS waits forever for audio. voice_image.py itself has to be in /root too — it defines `image` (used at build time on the local machine) AND is imported at runtime in the container. ws_ticket/ is the SAME package backend uses (`app/services/ws_ticket/`), bundled into the image so both sides sign with identical logic.
    .add_local_dir("app/services/ws_ticket", remote_path="/root/ws_ticket")
    .add_local_file(
        "inference/ticket_auth_middleware.py", remote_path="/root/ticket_auth_middleware.py"
    )
    .add_local_file(
        "inference/start_aiohttp_in_thread.py", remote_path="/root/start_aiohttp_in_thread.py"
    )
    .add_local_file("inference/voice_image.py", remote_path="/root/voice_image.py")
    .add_local_file("inference/voice_app.py", remote_path="/root/voice_app.py")
    .add_local_file("inference/voice.py", remote_path="/root/voice.py")
    .add_local_file("inference/download_weights.py", remote_path="/root/download_weights.py")
    .add_local_file("inference/warm_voice.py", remote_path="/root/warm_voice.py")
    .add_local_file(
        "inference/inactivity_thresholds.py", remote_path="/root/inactivity_thresholds.py"
    )
    .add_local_file("inference/boost_loudness.py", remote_path="/root/boost_loudness.py")
    .add_local_file(
        "inference/compute_scaledown_window.py", remote_path="/root/compute_scaledown_window.py"
    )
)
