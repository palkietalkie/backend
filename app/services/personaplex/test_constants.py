import re
from pathlib import Path

from app.services.personaplex.constants import PERSONAPLEX_MODEL


def test_personaplex_model_matches_inference_hf_repo() -> None:
    # The value start_conversation records on a session for cost analysis must be the SAME model the inference plane actually loads.
    # If someone bumps the served model (e.g. a v2) but forgets this constant, analytics would silently attribute sessions to a model that never ran.
    # Read the inference source as text (importing it pulls Modal + torch, unavailable in the unit env) and assert the two stay in lockstep.
    repo_root = Path(__file__).resolve().parents[3]
    voice_app = (repo_root / "inference" / "voice_app.py").read_text()
    match = re.search(r'HF_REPO\s*=\s*"([^"]+)"', voice_app)
    assert match is not None, "HF_REPO not found in inference/voice_app.py"
    assert match.group(1) == PERSONAPLEX_MODEL
