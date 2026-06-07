"""PersonaPlex decoding hyperparameters.

Pure value object. No httpx / FastAPI / network imports — directly testable.

Defaults match the upstream NVIDIA reference client (``github.com/NVIDIA/personaplex``); tune only if Audio QA shows a regression."""

from dataclasses import asdict, dataclass

DEFAULT_TEXT_TEMPERATURE = 0.8
DEFAULT_TEXT_TOPK = 25
DEFAULT_AUDIO_TEMPERATURE = 0.8
DEFAULT_AUDIO_TOPK = 250
DEFAULT_PAD_MULT = 1
DEFAULT_TEXT_SEED = 42
DEFAULT_AUDIO_SEED = 42
DEFAULT_REPETITION_PENALTY_CONTEXT = 64
DEFAULT_REPETITION_PENALTY = 1.0


@dataclass(frozen=True)
class SamplingParams:
    text_temperature: float = DEFAULT_TEXT_TEMPERATURE
    text_topk: int = DEFAULT_TEXT_TOPK
    audio_temperature: float = DEFAULT_AUDIO_TEMPERATURE
    audio_topk: int = DEFAULT_AUDIO_TOPK
    pad_mult: int = DEFAULT_PAD_MULT
    text_seed: int = DEFAULT_TEXT_SEED
    audio_seed: int = DEFAULT_AUDIO_SEED
    repetition_penalty_context: int = DEFAULT_REPETITION_PENALTY_CONTEXT
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY

    def as_query_params(self) -> dict[str, str]:
        return {k: str(v) for k, v in asdict(self).items()}


# Pre-computed mapping for callers that want the defaults without instantiating a dataclass.
DEFAULT_DECODING_PARAMS: dict[str, str] = SamplingParams().as_query_params()
