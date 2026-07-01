"""How often the tutor corrects language gaps. 5 levels. Default derived from proficiency.

A BASELINE only: the persona still overrides it by situation (the 'Be a real partner first' rules in assemble_prompt), so even at `always` it won't correct mid-vent or dodge a real question, and even at `rarely` it flags a serious error. The level sets HOW OFTEN; the situational rules decide WHEN TO HOLD BACK regardless.

Stored as a named slug like every other lever (proficiency, tutor_speaking_speed), NOT a raw number. The 0/25/50/75/100% the user sees is a display concern (`CORRECTION_FREQUENCY_PERCENT`) the options endpoint returns, exactly like the speed playback-rate map, and never the stored value.
"""

from typing import Literal, get_args

from app.profile.proficiency import Proficiency

CorrectionFrequency = Literal[
    "never",
    "rarely",
    "sometimes",
    "often",
    "always",
]

ALL_CORRECTION_FREQUENCIES: frozenset[CorrectionFrequency] = frozenset(
    get_args(CorrectionFrequency)
)

# What the user sees per level. Display only; storage is the slug. iOS renders this instead of hardcoding the ladder, so the client can never drift from the server's steps.
CORRECTION_FREQUENCY_PERCENT: dict[CorrectionFrequency, int] = {
    "never": 0,
    "rarely": 25,
    "sometimes": 50,
    "often": 75,
    "always": 100,
}

# The baseline-density sentence woven into the prompt's Natural-phrasing section per level. `never` is empty because assemble_prompt swaps the whole teaching section for a corrections-off note at that level rather than inserting a sentence.
CORRECTION_FREQUENCY_PROMPT: dict[CorrectionFrequency, str] = {
    "never": "",
    "rarely": "Correct very sparingly, only a mistake serious enough to actually cause a misunderstanding. The rest of the time just talk; let small errors and merely-unnatural phrasing go.",
    "sometimes": "Correct the notable gaps and clear errors, but let the minor or merely-stylistic ones slide, roughly the bigger half of what you notice.",
    "often": "Correct most gaps, clear errors and unnatural phrasing alike; let only the tiniest things pass.",
    "always": "Correct essentially every gap you notice, every turn: they want to be caught on everything. Still weave each fix into the conversation, never a dry drill.",
}

# Neutral middle, matching the column default. Used when a stored value is stale/missing.
DEFAULT_CORRECTION_FREQUENCY: CorrectionFrequency = "sometimes"

# Suggested starting level per proficiency, used by onboarding to pre-select (users adjust anytime). A real beginner shouldn't be buried in corrections; an advanced user came to be pushed. Intermediate sits at the neutral 'sometimes' (50%), which is also the column default.
DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY: dict[Proficiency, CorrectionFrequency] = {
    "beginner": "rarely",
    "lower_intermediate": "sometimes",
    "intermediate": "sometimes",
    "upper_intermediate": "often",
    "advanced": "always",
}

_BY_NAME: dict[str, CorrectionFrequency] = {s: s for s in ALL_CORRECTION_FREQUENCIES}


def coerce_correction_frequency(raw: str | None) -> CorrectionFrequency:
    """Narrow the plain-`str` DB value to the Literal without a cast, defaulting a stale/missing value to the neutral middle. Mirrors `coerce_speaking_speed`."""
    return _BY_NAME.get(raw or "", DEFAULT_CORRECTION_FREQUENCY)
