# OpenAI Realtime audio token rates, USD per 1M tokens, keyed by model: (input, output). Single source of truth for session-cost math, mirroring root CLAUDE.md § Cost simulation. Cached input is billed lower ($0.30/M on mini) but the reported usage doesn't split cached vs uncached yet, so input cost is a slight over-estimate.
REALTIME_RATES_USD_PER_M: dict[str, tuple[float, float]] = {
    "gpt-realtime-mini": (10.0, 20.0),
    "gpt-realtime-2": (32.0, 64.0),
    "gpt-realtime": (32.0, 64.0),
}


def compute_realtime_cost(
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> tuple[float, float] | None:
    # (input_cost_usd, output_cost_usd) for a session, or None when cost can't be computed — no token counts (PersonaPlex bills via Modal GPU-time, or the session never reported usage) or a model with no known rate. The caller stores NULL cost then, never a misleading 0.
    if input_tokens is None or output_tokens is None:
        return None
    rate = REALTIME_RATES_USD_PER_M.get(model or "")
    if rate is None:
        return None
    input_rate, output_rate = rate
    return input_tokens / 1_000_000 * input_rate, output_tokens / 1_000_000 * output_rate
