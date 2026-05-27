import os

import modal
from voice_app import HF_REPO, IMAGE, app, weights_volume


@app.function(
    image=IMAGE,
    volumes={"/weights": weights_volume},
    secrets=[modal.Secret.from_name("huggingface")],
    timeout=60 * 30,
)
def download_weights() -> None:
    # One-time per Modal Volume: pull nvidia/personaplex-7b-v1 weights. Run after `modal deploy` and before first inference.
    from huggingface_hub import snapshot_download

    print(f"[weights] downloading {HF_REPO} → /weights")
    snapshot_download(
        repo_id=HF_REPO,
        cache_dir="/weights",
        token=os.environ["HF_TOKEN"],
        max_workers=8,
    )
    weights_volume.commit()
    print("[weights] commit complete")
