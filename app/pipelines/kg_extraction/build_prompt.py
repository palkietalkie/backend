from app.pipelines.kg_extraction.constants import PROMPT_HEADER


def build_prompt(turns: str) -> str:
    return PROMPT_HEADER + turns
