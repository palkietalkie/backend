"""TypedDicts mirroring the SQL schema (migrations/0001_initial.sql + diffs).

Hand-written for now; long-term plan is typegen from Neon. Each TypedDict matches the columns of one table; nullable columns are typed with ``| None``.
"""

import uuid
from datetime import datetime
from typing import Any, TypedDict


class UserRow(TypedDict):
    id: uuid.UUID
    clerk_user_id: str
    email: str | None
    premium: bool
    premium_ends_at: datetime | None
    created_at: datetime
    updated_at: datetime
    display_name: str | None
    name_pronunciation: str | None
    native_language: str | None
    target_accent: str | None
    goals: str | None
    location_city: str | None
    timezone: str | None
    personalization_consent: datetime | None
    product_improvement_consent: datetime | None
    consent_screen_seen_at: datetime | None


class PersonaRow(TypedDict):
    id: uuid.UUID
    name: str
    description: str
    voice_id: str
    role: str | None
    age: str | None
    background: str | None
    vocabulary_register: str | None
    conversational_style: str | None
    topical_preferences: str | None
    is_public: bool
    like_count: int
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PersonaLikeRow(TypedDict):
    id: uuid.UUID
    user_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime


class ConversationSessionRow(TypedDict):
    id: uuid.UUID
    user_id: uuid.UUID
    persona_id: uuid.UUID | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None


class TranscriptRow(TypedDict):
    id: int
    session_id: uuid.UUID
    role: str
    text: str
    ts: datetime


class WordFreqRow(TypedDict):
    user_id: uuid.UUID
    lemma: str
    count: int
    last_used_at: datetime


class PhraseFreqRow(TypedDict):
    user_id: uuid.UUID
    phrase: str
    count: int
    last_used_at: datetime


class MistakeRow(TypedDict):
    id: uuid.UUID
    user_id: uuid.UUID
    original: str
    corrected: str
    category: str
    count: int
    last_seen_at: datetime


class CefrVocabRow(TypedDict):
    lemma: str
    level: str


class CefrFrequencyRow(TypedDict):
    lemma: str
    rank: int


class EventRow(TypedDict):
    id: int
    user_id: uuid.UUID | None
    event_type: str
    ts: datetime
    props: dict[str, Any]


class DeviceTokenRow(TypedDict):
    id: uuid.UUID
    user_id: uuid.UUID
    apns_token: str
    created_at: datetime


class CalendarTokenRow(TypedDict):
    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
