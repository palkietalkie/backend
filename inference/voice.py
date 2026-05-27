"""Modal @app.cls hosting NVIDIA's moshi/PersonaPlex server.

One container hosts one PersonaPlex; concurrent WebSocket sessions multiplex on the same GPU.
Modal autoscales horizontally when concurrency is saturated.

Frame protocol (matches NVIDIA's reference recv/send loops):
    client → server:  b"\\x01" + opus_bytes   (audio)
    server → client:  b"\\x00"                (handshake, sent once after system prompts)
                      b"\\x01" + opus_bytes   (generated audio)
                      b"\\x02" + utf8_text    (transcript piece)
"""

from __future__ import annotations

import os
import sys
import tarfile
import time

import modal
from voice_app import HF_REPO, IMAGE, SCALEDOWN_WINDOW, app, weights_volume


@app.cls(
    image=IMAGE,
    gpu="A100-80GB",
    volumes={"/weights": weights_volume},
    secrets=[
        modal.Secret.from_name("ws_ticket"),
        modal.Secret.from_name("huggingface"),
    ],
    scaledown_window=SCALEDOWN_WINDOW,
    timeout=60 * 30,
    min_containers=0,
)
@modal.concurrent(max_inputs=10)
class Voice:
    @modal.enter()
    def load_model(self) -> None:
        # Cold-start: load Mimi + Moshi LM weights from NVMe → A100 VRAM.
        start = time.time()
        hf_cache_dir = os.path.join("/weights", f"models--{HF_REPO.replace('/', '--')}")
        if not os.path.isdir(hf_cache_dir):
            weights_volume.reload()
            if not os.path.isdir(hf_cache_dir):
                raise RuntimeError(
                    f"Weights missing at {hf_cache_dir}. Run download_weights first."
                )

        import sentencepiece
        import torch
        from huggingface_hub import hf_hub_download
        from moshi.models import loaders

        # NVIDIA's reference server.py wraps main() in `with torch.no_grad():`. We strip that wrapper (would boot a second CLI server on module import), so disable gradient tracking ourselves. start_aiohttp_in_thread also sets this in the aiohttp thread (PyTorch's flag is thread-local).
        torch.set_grad_enabled(False)

        mimi_path = hf_hub_download(HF_REPO, loaders.MIMI_NAME)
        moshi_path = hf_hub_download(HF_REPO, loaders.MOSHI_NAME)
        tokenizer_path = hf_hub_download(HF_REPO, loaders.TEXT_TOKENIZER_NAME)
        voices_tgz_path = hf_hub_download(HF_REPO, "voices.tgz")

        # Extract voices once (idempotent). Mirrors _get_voice_prompt_dir in NVIDIA's server.
        voices_dir = os.path.join(os.path.dirname(voices_tgz_path), "voices")
        if not os.path.isdir(voices_dir):
            # Extracting NVIDIA's voices.tgz fetched from their gated HF repo — trusted source we explicitly download.
            with tarfile.open(voices_tgz_path, "r:gz") as tar:
                tar.extractall(path=os.path.dirname(voices_tgz_path))  # noqa: S202
        self._voice_prompt_dir = voices_dir

        self._mimi = loaders.get_mimi(mimi_path, device="cuda")
        self._other_mimi = loaders.get_mimi(mimi_path, device="cuda")
        self._lm = loaders.get_moshi_lm(moshi_path, device="cuda")
        self._lm.eval()
        self._text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer_path)  # type: ignore[call-arg]
        elapsed = time.time() - start
        print(f"[load] PersonaPlex ready on cuda in {elapsed:.2f}s", file=sys.stderr)

    @modal.web_server(port=8000, label="api", startup_timeout=60)
    def serve(self) -> None:
        # aiohttp/torch/moshi only exist in the container — these have to be lazy-imported here so `modal deploy` from a dev laptop doesn't fail on the missing deps.
        import torch
        from aiohttp import web
        from moshi.server import ServerState
        from start_aiohttp_in_thread import start_aiohttp_in_thread
        from ticket_auth_middleware import ticket_auth_middleware

        # ServerState.warmup() reads self.device.type — pass a real torch.device, NOT a string.
        state = ServerState(
            mimi=self._mimi,
            other_mimi=self._other_mimi,
            text_tokenizer=self._text_tokenizer,
            lm=self._lm,
            device=torch.device("cuda"),
            voice_prompt_dir=self._voice_prompt_dir,
            save_voice_prompt_embeddings=False,
        )
        state.warmup()

        async def handle_health(_request):
            return web.json_response({"status": "ok", "model": HF_REPO})

        api_app = web.Application(middlewares=[ticket_auth_middleware])
        api_app.router.add_get("/health", handle_health)
        api_app.router.add_get("/api/chat", state.handle_chat)

        start_aiohttp_in_thread(api_app, port=8000)
