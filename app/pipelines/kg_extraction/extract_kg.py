import httpx

from app.pipelines.kg_extraction.build_prompt import build_prompt
from app.pipelines.kg_extraction.parse_payload import parse_payload
from app.services.gemma.complete_json import complete_json
from app.services.neo4j.models import KGEntity, KGRelation


async def extract_kg(texts: list[str]) -> tuple[list[KGEntity], list[KGRelation]]:
    # LLM call + parse. Returns empty lists on outage or no findings.
    if not texts:
        return [], []
    prompt = build_prompt("\n".join(f"- {t}" for t in texts))
    try:
        data = await complete_json(prompt, max_tokens=2048)
    except httpx.HTTPError:
        return [], []
    return parse_payload(data)
