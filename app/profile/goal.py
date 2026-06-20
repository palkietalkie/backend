"""Preset practice goals offered in onboarding + Practice as multi-select chips.

These are the suggested presets only. The stored `users.goals` is a `TEXT[]` that holds any mix of these slugs PLUS free-text entries the user typed under "Other", so the column itself is not constrained to this Literal (free text wouldn't match). iOS shows these as chips and renders any non-matching array element as the user's "Other" text."""

from typing import Literal, get_args

Goal = Literal[
    "everyday_conversation",
    "making_friends",
    "dating_relationships",
    "family",
    "work_meetings",
    "job_interview",
    "public_speaking",
    "living_abroad",
    "studying_abroad",
    "travel",
]

ALL_GOALS: frozenset[Goal] = frozenset(get_args(Goal))

# Readable phrases for the system prompt. The slug is a stable wire/storage value; the tutor must hear a natural phrase, never "dating_relationships". Free-text "Other" entries pass through unchanged.
GOAL_PROMPT_PHRASES: dict[Goal, str] = {
    "everyday_conversation": "everyday conversation",
    "making_friends": "making friends and socializing",
    "dating_relationships": "dating and relationships",
    "family": "talking with family and in-laws",
    "work_meetings": "work, meetings, and email",
    "job_interview": "job interviews",
    "public_speaking": "public speaking and presentations",
    "living_abroad": "settling into life abroad",
    "studying_abroad": "studying abroad",
    "travel": "travel",
}
