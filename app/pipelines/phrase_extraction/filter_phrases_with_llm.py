import httpx

from app.services.gemma.complete_json import complete_json


async def filter_phrases_with_llm(candidates: list[str]) -> list[str]:
    # Returns the subset to keep. Degrades gracefully — on LLM outage returns all candidates.
    if not candidates:
        return []
    prompt = (
        "From this list of candidate English phrases, return the subset that are natural "
        "multi-word expressions a learner should remember (idioms, collocations, phrasal verbs). "
        'Drop generic compositional phrases. Return JSON: {"keep": ["phrase1", ...]}.\n\n'
        + "\n".join(f"- {p}" for p in candidates)
    )
    try:
        data = await complete_json(prompt)
    except httpx.HTTPError:
        return candidates
    keep = data.get("keep") or []
    return [str(p) for p in keep if isinstance(p, str)]
