"""PersonaPlex WebSocket URL construction.

Pure string assembly. No FastAPI or network imports — directly testable.

URL format (verified against ``github.com/NVIDIA/personaplex``):

    ws(s)://{PERSONAPLEX_HOST}/api/chat
        ?text_prompt={url-encoded persona + situational context}
        &voice_prompt={voice_id_or_prompt}
        &auth_token={clerk_jwt}
        &text_temperature=0.8
        &text_topk=25
        &audio_temperature=0.8
        &audio_topk=250
        &pad_mult=1
        &text_seed=42
        &audio_seed=42
        &repetition_penalty_context=64
        &repetition_penalty=1.0
"""

from urllib.parse import urlencode

from app.services.personaplex.sampling import DEFAULT_DECODING_PARAMS

PATH = "/api/chat"


def build_ws_url(
    base: str,
    *,
    text_prompt: str,
    voice_id: str,
    auth_token: str | None,
    decoding_params: dict[str, str] | None = None,
) -> str:
    # NVIDIA's reference server expects voice_prompt as the actual filename inside voices.tgz (e.g. NATM1.pt). Append .pt unless the caller already provided an extension.
    voice_prompt_filename = voice_id if voice_id.endswith((".pt", ".wav")) else f"{voice_id}.pt"
    params: dict[str, str] = {
        "text_prompt": text_prompt,
        "voice_prompt": voice_prompt_filename,
        "auth_token": auth_token or "",
        **(decoding_params or DEFAULT_DECODING_PARAMS),
    }
    # ``safe=""`` percent-encodes everything including newlines / punctuation in text_prompt.
    query = urlencode(params, safe="")
    return f"{base}{PATH}?{query}"
