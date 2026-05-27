from app.pipelines.mistake_detection.constants import PROMPT_HEADER


def build_prompt(turns: str) -> str:
    return PROMPT_HEADER + turns
