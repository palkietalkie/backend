import logging
import uuid
from datetime import UTC, datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from neo4j.exceptions import GqlError
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.routers.conversation.assemble_prompt import PersonaPromptFields, assemble_prompt
from app.routers.conversation.constants import (
    INSERT_EVENT_SQL,
    PROVIDER_OPENAI,
    PROVIDER_PERSONAPLEX,
)
from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.calendar.fetch_todays_events import fetch_todays_events
from app.services.neo4j.fetch_entities_summary import fetch_entities_summary
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.make_rows import make_persona_row
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_this_week import sum_seconds_used_this_week
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today
from app.services.openai.constants import OpenAIVoiceId
from app.services.openai.mint_session import mint_openai_session
from app.services.personaplex.build_handshake import build_handshake
from app.services.weather.fetch_weather import fetch_weather
from app.services.ws_ticket.mint_ws_ticket import mint_ws_ticket

router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = logging.getLogger(__name__)


class StartRequest(BaseModel):
    persona_id: uuid.UUID
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    topic_override: str | None = Field(default=None, max_length=500)


class StartResponse(BaseModel):
    session_id: uuid.UUID
    text_prompt: str
    voice_id: str
    ws_url: str
    # "openai" → iOS speaks the JSON event protocol against OpenAI Realtime. "personaplex" → iOS speaks the binary Ogg-Opus protocol against Modal. Switched server-side via INFERENCE_PROVIDER env var.
    provider: str
    # Populated only when provider == "openai". Short-lived (~1 min) client_secret.value from OpenAI's /v1/realtime/sessions response. iOS attaches it as Authorization: Bearer ... on the WS upgrade. Empty for personaplex.
    ephemeral_token: str | None = None


@router.post("/start", response_model=StartResponse)
async def start_conversation(
    body: StartRequest,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> StartResponse:
    settings = get_settings()
    # Free-plan caps. Two windows apply — the daily one resets at user-local midnight, the weekly one at user-local Monday 00:00. Whichever the user hits first stops them; rejecting here (rather than mid-conversation) keeps the iOS UX simple: either you get a session or you get an "out of time" screen with an Upgrade CTA.
    if not check_is_premium_now(user):
        used_today = await sum_seconds_used_today(user, db)
        if used_today >= FREE_MINUTES_PER_DAY * 60:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"daily free limit reached ({FREE_MINUTES_PER_DAY} min). upgrade or come back at local midnight.",
            )
        used_this_week = await sum_seconds_used_this_week(user, db)
        if used_this_week >= FREE_MINUTES_PER_WEEK * 60:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"weekly free limit reached ({FREE_MINUTES_PER_WEEK} min). upgrade or come back next Monday.",
            )
    provider = settings.inference_provider.lower()
    preset = find_preset_by_id(body.persona_id)
    persona_voice_id: str
    persona_fields: PersonaPromptFields
    if preset is not None:
        persona_voice_id = preset.voice_for(provider)
        persona_fields = PersonaPromptFields(
            name=preset.name,
            role=preset.role,
            age=preset.age,
            background=preset.background,
            vocabulary_register=preset.vocabulary_register,
            conversational_style=preset.conversational_style,
            topical_preferences=preset.topical_preferences,
        )
    else:
        persona_row_raw = await db.fetchrow(
            """SELECT id, name, description, voice_id, role, age, background,
                      vocabulary_register, conversational_style, topical_preferences,
                      is_public, like_count, user_id, created_at, updated_at
               FROM personas
               WHERE id = $1""",
            body.persona_id,
        )
        if persona_row_raw is None:
            logger.warning(
                "persona %s not in presets and not in DB (user=%s)",
                body.persona_id,
                user["id"],
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="persona not found")
        persona_row = make_persona_row(persona_row_raw)
        if persona_row["user_id"] != user["id"] and not persona_row["is_public"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="persona not owned by user"
            )
        persona_voice_id = persona_row["voice_id"]
        persona_fields = PersonaPromptFields(
            name=persona_row["name"],
            role=persona_row["role"],
            age=persona_row["age"],
            background=persona_row["background"],
            vocabulary_register=persona_row["vocabulary_register"],
            conversational_style=persona_row["conversational_style"],
            topical_preferences=persona_row["topical_preferences"],
        )

    weather = None
    if body.lat is not None and body.lon is not None:
        weather = await fetch_weather(body.lat, body.lon)
    weather_label = (
        f"{weather.temperature_c:.0f}°C, {weather.label}, {'day' if weather.is_day else 'night'}"
        if weather
        else None
    )

    try:
        kg_entities = await fetch_entities_summary(user["id"])
    except GqlError:
        # GqlError covers both `Neo4jError` (server-side response errors) and `DriverError` (connection / DNS / auth / config failures). KG enrichment is best-effort — don't 500 the conversation start when Neo4j is unreachable.
        kg_entities = []

    try:
        events = await fetch_todays_events(user, db)
    except asyncpg.PostgresError:
        events = []
    event_titles = [e.title for e in events]

    # Recall the user's last 3 conversations WITH THIS SAME PERSONA. Each persona has their own memory of the user — Aiden doesn't get fed Naoko's transcript tail. Pulling 3 not 1 so the persona has shared history beyond the very last chat; longer-term recall (per-session summaries + vector search) is the planned upgrade in /CLAUDE.md.
    last_rows = await db.fetch(
        """SELECT id, started_at, ended_at
           FROM conversation_sessions
           WHERE user_id = $1 AND persona_id = $2 AND ended_at IS NOT NULL
           ORDER BY ended_at DESC
           LIMIT 3""",
        user["id"],
        body.persona_id,
    )
    recent_recall: str | None = None
    if last_rows:
        session_tails: list[str] = []
        for session_row in reversed(last_rows):
            transcript_rows = await db.fetch(
                """SELECT speaker, text
                   FROM transcripts
                   WHERE session_id = $1
                   ORDER BY started_at DESC
                   LIMIT 10""",
                session_row["id"],
            )
            if not transcript_rows:
                continue
            ordered = list(reversed(transcript_rows))
            joined = " | ".join(f"{t['speaker']}: {t['text'][:200]}" for t in ordered)
            session_tails.append(joined)
        if session_tails:
            recent_recall = "\n---\n".join(session_tails)

    text_prompt = assemble_prompt(
        persona_fields,
        user,
        kg_entities,
        weather_label,
        event_titles,
        recent_recall=recent_recall,
        topic_override=body.topic_override,
    )

    now = datetime.now(UTC)
    session_id = uuid.uuid4()
    async with db.transaction():
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, persona_id, started_at)
               VALUES ($1, $2, $3, $4)
               RETURNING id, user_id, persona_id, started_at, ended_at, duration_seconds""",
            session_id,
            user["id"],
            body.persona_id,
            now,
        )
        await db.execute(
            INSERT_EVENT_SQL,
            user["id"],
            "conversation_start",
            now,
            {"persona_id": str(body.persona_id), "voice_id": persona_voice_id},
        )

    if provider == PROVIDER_OPENAI:
        try:
            openai_voice = OpenAIVoiceId(persona_voice_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"voice_id {persona_voice_id!r} is not an OpenAI voice",
            ) from e
        openai_session = await mint_openai_session(
            text_prompt=text_prompt,
            voice_id=openai_voice,
            is_premium=bool(user["premium"]),
        )
        return StartResponse(
            session_id=session_id,
            text_prompt=text_prompt,
            voice_id=persona_voice_id,
            ws_url=openai_session.ws_url,
            provider=PROVIDER_OPENAI,
            ephemeral_token=openai_session.ephemeral_token,
        )

    ws_ticket = mint_ws_ticket(str(user["id"]))
    handshake = build_handshake(
        text_prompt=text_prompt,
        voice_id=persona_voice_id,
        auth_token=ws_ticket,
    )
    return StartResponse(
        session_id=session_id,
        text_prompt=handshake.text_prompt,
        voice_id=handshake.voice_id,
        ws_url=handshake.ws_url,
        provider=PROVIDER_PERSONAPLEX,
        ephemeral_token=None,
    )
