"""PersonaPlex client tests.

URL construction is pure — assert the exact percent-encoded query string. JWT propagation is asserted through the same path (the JWT goes into the ``auth_token`` query param)."""

from urllib.parse import parse_qs, urlparse

from app.config import Settings
from app.services.personaplex.build_handshake import PersonaPlexHandshake, build_handshake
from app.services.personaplex.build_ws_url import build_ws_url
from app.services.personaplex.sampling import DEFAULT_DECODING_PARAMS, SamplingParams


def test_sampling_params_defaults_round_trip() -> None:
    params = SamplingParams()
    out = params.as_query_params()
    # Every value must be a string so urlencode can use it directly.
    assert all(isinstance(v, str) for v in out.values())
    assert out["text_temperature"] == "0.8"
    assert out["text_topk"] == "25"
    assert out["audio_temperature"] == "0.8"
    assert out["audio_topk"] == "250"
    assert out["pad_mult"] == "1"
    assert out["text_seed"] == "42"
    assert out["audio_seed"] == "42"
    assert out["repetition_penalty_context"] == "64"
    assert out["repetition_penalty"] == "1.0"


def test_default_decoding_params_match_sampling() -> None:
    assert SamplingParams().as_query_params() == DEFAULT_DECODING_PARAMS


def test_build_ws_url_includes_all_required_params() -> None:
    url = build_ws_url(
        "wss://personaplex.test",
        text_prompt="Hello world",
        voice_id="NATM1",
        auth_token="jwt-token-abc",
    )
    parsed = urlparse(url)
    assert parsed.scheme == "wss"
    assert parsed.netloc == "personaplex.test"
    assert parsed.path == "/api/chat"

    qs = parse_qs(parsed.query)
    assert qs["text_prompt"] == ["Hello world"]
    # voice_prompt gets .pt suffix — NVIDIA's server reads it as a filename.
    assert qs["voice_prompt"] == ["NATM1.pt"]
    assert qs["auth_token"] == ["jwt-token-abc"]
    # decoding hyperparameters all present
    for key in DEFAULT_DECODING_PARAMS:
        assert qs[key] == [DEFAULT_DECODING_PARAMS[key]]


def test_build_ws_url_percent_encodes_multiline_prompt() -> None:
    prompt = "Line one\nLine two with spaces & ampersand"
    url = build_ws_url(
        "wss://personaplex.test",
        text_prompt=prompt,
        voice_id="NATF1",
        auth_token="",
    )
    # urlencode with safe="" must escape the newline + ampersand; space encodes as '+'
    assert "%0A" in url  # newline
    assert "+" in urlparse(url).query  # space-as-plus
    assert "%26" in url  # ampersand
    qs = parse_qs(urlparse(url).query)
    assert qs["text_prompt"] == [prompt]


def test_build_ws_url_empty_auth_token_when_none() -> None:
    url = build_ws_url(
        "wss://personaplex.test",
        text_prompt="x",
        voice_id="V",
        auth_token=None,
    )
    qs = parse_qs(urlparse(url).query, keep_blank_values=True)
    assert qs["auth_token"] == [""]


def test_build_ws_url_accepts_override_decoding_params() -> None:
    custom = SamplingParams(text_temperature=0.5).as_query_params()
    url = build_ws_url(
        "wss://personaplex.test",
        text_prompt="x",
        voice_id="V",
        auth_token="t",
        decoding_params=custom,
    )
    qs = parse_qs(urlparse(url).query)
    assert qs["text_temperature"] == ["0.5"]


def test_build_handshake_returns_dataclass(settings: Settings) -> None:
    handshake = build_handshake(
        text_prompt="System prompt body",
        voice_id="NATM1",
        auth_token="jwt-xyz",
    )
    assert isinstance(handshake, PersonaPlexHandshake)
    assert handshake.text_prompt == "System prompt body"
    assert handshake.voice_id == "NATM1"
    assert handshake.ws_url.startswith(settings.personaplex_ws_base + "/api/chat?")
    qs = parse_qs(urlparse(handshake.ws_url).query)
    assert qs["auth_token"] == ["jwt-xyz"]


def test_build_handshake_propagates_jwt_into_url(settings: Settings) -> None:
    jwt = "eyJhbGciOiJSUzI1NiJ9.payload.sig"
    handshake = build_handshake(text_prompt="x", voice_id="V", auth_token=jwt)
    qs = parse_qs(urlparse(handshake.ws_url).query)
    assert qs["auth_token"] == [jwt]
