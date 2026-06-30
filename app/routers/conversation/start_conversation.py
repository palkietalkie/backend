import asyncio
import logging
import random
import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.personas.voices.list_voices_for_provider import list_voices_for_provider
from app.profile.tutor_speaking_speed import coerce_speaking_speed
from app.routers.conversation.assemble_prompt import PersonaPromptFields, assemble_prompt
from app.routers.conversation.constants import (
    INSERT_EVENT_SQL,
    PROVIDER_OPENAI,
    PROVIDER_PERSONAPLEX,
    Provider,
)
from app.routers.conversation.fetch_recent_recall import fetch_recent_recall
from app.routers.conversation.resolve_free_cap import resolve_free_cap
from app.services.calendar.fetch_todays_events import fetch_todays_events
from app.services.neo4j.fetch_entities_summary import fetch_entities_summary
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.make_rows import make_persona_row
from app.services.neon.rows import UserRow
from app.services.openai.constants import OPENAI_REALTIME_MODEL_PAID, OpenAIVoiceId
from app.services.openai.mint_openai_session import mint_openai_session
from app.services.personaplex.build_handshake import build_handshake
from app.services.personaplex.constants import PERSONAPLEX_MODEL
from app.services.slack.format_user_label import format_user_label
from app.services.slack.post_session_threaded import post_session_threaded
from app.services.ws_ticket.mint_ws_ticket import mint_ws_ticket

router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = logging.getLogger(__name__)


class StartRequest(BaseModel):
    persona_id: uuid.UUID
    # The device's live location. Weather (its only former consumer) was removed; kept here, unused for now, for the live-city feature (the persona knowing where the user actually is — see the prompt's Location line, which still falls back to the stale profile city).
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    # Generous bound (was 500, which truncated news summaries): the topic hook should carry the full story, not a headline. Still capped so the prompt can't be ballooned arbitrarily.
    topic_override: str | None = Field(default=None, max_length=8000)


class StartResponse(BaseModel):
    session_id: uuid.UUID
    text_prompt: str
    voice_id: str
    ws_url: str
    # "openai" → iOS speaks the JSON event protocol against OpenAI Realtime. "personaplex" → iOS speaks the binary Ogg-Opus protocol against Modal. Switched server-side via INFERENCE_PROVIDER env var. Literal (not str) so the value is constrained at the source of truth: it surfaces as an enum in /openapi.json, the generated iOS type, and a bad value can never reach the client (where the branch silently falls through to PersonaPlex).
    provider: Provider
    # Populated only when provider == "openai". Short-lived (~1 min) client_secret.value from OpenAI's /v1/realtime/sessions response. iOS attaches it as Authorization: Bearer ... on the WS upgrade. Empty for personaplex.
    ephemeral_token: str | None = None
    # Free-tier time left this session before a cap (daily or weekly, whichever is tighter) stops them, in seconds. iOS counts down from this to wrap up ~30s early and show the limit screen. None = unlimited (premium).
    free_seconds_remaining: int | None = None
    # Which cap that countdown belongs to, so iOS shows the right message ("back tomorrow" for daily vs "back Monday" for weekly — the weekly block is longer and must read clearly). None = unlimited (premium).
    free_limit_kind: Literal["daily", "weekly"] | None = None


@router.post("/start", response_model=StartResponse)
async def start_conversation(
    body: StartRequest,
    background_tasks: BackgroundTasks,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> StartResponse:
    settings = get_settings()
    # Free-plan caps: raises 402 if the user is out of time, else hands back the countdown + which cap it is (None for premium). iOS uses these to wrap up ~30s early and show the right limit screen.
    free_seconds_remaining, free_limit_kind = await resolve_free_cap(user, db)
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

    # Topic sessions drop the carried-over persona character (assemble_prompt neutralizes it) and so have no persona voice to ride on. Pick a fresh random voice from the active provider's catalog so each topic session still has an acoustic identity instead of defaulting to the last persona's voice.
    topic_mode = body.topic_override is not None
    if topic_mode:
        persona_voice_id = random.choice(list_voices_for_provider(provider)).id  # noqa: S311

    # Recall is awaited after the gather, not inside it: it shares the request's single asyncpg connection with calendar, and one connection runs only one query at a time. KG and calendar use distinct connections, so they gather safely.
    kg_entities, events = await asyncio.gather(
        fetch_entities_summary(user["id"]),
        fetch_todays_events(user, db),
    )
    event_titles = [e.title for e in events]

    # Skipped in topic mode: a Today-screen topic is a deliberate fresh start, so feeding the last conversation's tail would pull the session back into the old subject (and assemble_prompt would discard it anyway).
    recent_recall = (
        None
        if topic_mode
        else await fetch_recent_recall(user["id"], body.persona_id, user["target_language"], db)
    )

    text_prompt = assemble_prompt(
        persona_fields,
        user,
        kg_entities,
        event_titles,
        recent_recall=recent_recall,
        topic_override=body.topic_override,
    )

    now = datetime.now(UTC)
    session_id = uuid.uuid4()
    # Record which model the session runs on: the OpenAI realtime model (same constant mint uses) or the PersonaPlex model on Modal. PersonaPlex bills through Modal and reports no token usage, but the model itself is still worth recording to tell the two paths apart in analysis.
    session_model = OPENAI_REALTIME_MODEL_PAID if provider == PROVIDER_OPENAI else PERSONAPLEX_MODEL
    async with db.transaction():
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, persona_id, started_at, target_language, model)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id, user_id, persona_id, started_at, ended_at, duration_seconds""",
            session_id,
            user["id"],
            body.persona_id,
            now,
            user["target_language"],
            session_model,
        )
        await db.execute(
            INSERT_EVENT_SQL,
            user["id"],
            "conversation_start",
            now,
            {"persona_id": str(body.persona_id), "voice_id": persona_voice_id},
        )

    # Open the session's Slack thread: this start message is the root every later session event (tool calls, errors) replies under, so one conversation stays in one thread. Fire-and-forget AFTER the response (BackgroundTasks) so the Slack POST never enters the latency-critical /start path; post_message itself no-ops outside production.
    background_tasks.add_task(
        post_session_threaded,
        settings.slack_channel_gtm,
        f":speech_balloon: *conversation_start* — {format_user_label(user)} `persona={persona_fields.name}`",
        str(session_id),
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
            speaking_speed=coerce_speaking_speed(user["tutor_speaking_speed"]),
        )
        return StartResponse(
            session_id=session_id,
            text_prompt=text_prompt,
            voice_id=persona_voice_id,
            ws_url=openai_session.ws_url,
            provider=PROVIDER_OPENAI,
            ephemeral_token=openai_session.ephemeral_token,
            free_seconds_remaining=free_seconds_remaining,
            free_limit_kind=free_limit_kind,
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
        free_seconds_remaining=free_seconds_remaining,
        free_limit_kind=free_limit_kind,
    )
