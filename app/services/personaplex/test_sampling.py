"""Pure dataclass — lock the defaults so an accidental rename of one of the upstream-mirrored hyperparameters surfaces here instead of as an audio-quality regression in production."""

from dataclasses import asdict

from app.services.personaplex.sampling import (
    DEFAULT_AUDIO_SEED,
    DEFAULT_AUDIO_TEMPERATURE,
    DEFAULT_AUDIO_TOPK,
    DEFAULT_PAD_MULT,
    DEFAULT_REPETITION_PENALTY,
    DEFAULT_REPETITION_PENALTY_CONTEXT,
    DEFAULT_TEXT_SEED,
    DEFAULT_TEXT_TEMPERATURE,
    DEFAULT_TEXT_TOPK,
    SamplingParams,
)


def test_defaults_match_upstream_personaplex_reference_client() -> None:
    p = SamplingParams()
    assert p.text_temperature == DEFAULT_TEXT_TEMPERATURE == 0.8
    assert p.text_topk == DEFAULT_TEXT_TOPK == 25
    assert p.audio_temperature == DEFAULT_AUDIO_TEMPERATURE == 0.8
    assert p.audio_topk == DEFAULT_AUDIO_TOPK == 250
    assert p.pad_mult == DEFAULT_PAD_MULT == 1
    assert p.text_seed == DEFAULT_TEXT_SEED == 42
    assert p.audio_seed == DEFAULT_AUDIO_SEED == 42
    assert p.repetition_penalty_context == DEFAULT_REPETITION_PENALTY_CONTEXT == 64
    assert p.repetition_penalty == DEFAULT_REPETITION_PENALTY == 1.0


def test_is_frozen() -> None:
    p = SamplingParams()
    try:
        p.text_temperature = 0.1  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("SamplingParams should be frozen")


def test_overrides_apply() -> None:
    p = SamplingParams(text_temperature=0.5, audio_topk=100)
    assert p.text_temperature == 0.5
    assert p.audio_topk == 100
    # Untouched fields keep defaults.
    assert p.text_topk == DEFAULT_TEXT_TOPK


def test_asdict_round_trips_to_dict() -> None:
    p = SamplingParams()
    d = asdict(p)
    assert d["text_temperature"] == DEFAULT_TEXT_TEMPERATURE
    assert isinstance(d, dict)
