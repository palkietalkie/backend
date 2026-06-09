"""PersonaPlex handshake assembly.

Ties the WebSocket URL builder and decoding-hyperparameter defaults together. This is the only module in the package that touches ``app.config`` — keeping the URL/sampling submodules pure for easy testing.

The frame protocol on the resulting WebSocket is binary-prefixed (for reference only — the backend does not speak it; iOS does, and the server is NVIDIA's PersonaPlex):

    0x00  handshake
    0x01  audio    (Opus, 24 kHz mono, 20 ms VoIP frames)
    0x02  text
    0x03  control
    0x04  metadata
    0x05  error
    0x06  ping

JWT is passed in the URL query string (matches iOS networking and is the only WS-friendly auth method PersonaPlex supports out of the box). PersonaPlex validates the same Clerk JWT against Clerk's JWKS endpoint on every connection — same auth the user signed in with, propagated to the GPU server so only paying users can open audio streams."""

from dataclasses import dataclass

from app.config import get_settings
from app.services.personaplex.build_ws_url import build_ws_url
from app.services.personaplex.sampling import SamplingParams


@dataclass(frozen=True)
class PersonaPlexHandshake:
    text_prompt: str
    voice_id: str
    ws_url: str


def build_handshake(
    text_prompt: str,
    voice_id: str,
    *,
    auth_token: str | None = None,
    sampling: SamplingParams | None = None,
) -> PersonaPlexHandshake:
    settings = get_settings()
    decoding_params = sampling.as_query_params() if sampling is not None else None
    ws_url = build_ws_url(
        settings.personaplex_ws_base,
        text_prompt=text_prompt,
        voice_id=voice_id,
        auth_token=auth_token,
        decoding_params=decoding_params,
    )
    return PersonaPlexHandshake(text_prompt=text_prompt, voice_id=voice_id, ws_url=ws_url)
