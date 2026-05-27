"""FastAPI entry point. Wires all routers, CORS, lifespan."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.lifespan import lifespan
from app.routers.consent.fetch_consent import router as consent_fetch_router
from app.routers.consent.update_consent import router as consent_update_router
from app.routers.conversation.append_transcript import router as conversation_transcript_router
from app.routers.conversation.end_conversation import router as conversation_end_router
from app.routers.conversation.list_sessions import router as conversation_sessions_router
from app.routers.conversation.start_conversation import router as conversation_start_router
from app.routers.entitlement.fetch_entitlement import router as entitlement_router
from app.routers.fetch_kg import router as kg_router
from app.routers.fetch_today_content import router as content_router
from app.routers.integrations.connect_google_calendar import (
    router as integrations_connect_google_router,
)
from app.routers.integrations.connect_outlook import router as integrations_outlook_router
from app.routers.integrations.handle_google_calendar_callback import (
    router as integrations_google_callback_router,
)
from app.routers.integrations.list_integrations import router as integrations_list_router
from app.routers.integrations.push_apple_calendar_events import (
    router as integrations_apple_events_router,
)
from app.routers.list_voices import router as voices_router
from app.routers.personas.create_persona import router as personas_create_router
from app.routers.personas.delete_persona import router as personas_delete_router
from app.routers.personas.like_persona import router as personas_like_router
from app.routers.personas.list_personas import router as personas_list_router
from app.routers.personas.unlike_persona import router as personas_unlike_router
from app.routers.personas.update_persona import router as personas_update_router
from app.routers.profile.fetch_profile import router as profile_fetch_router
from app.routers.profile.update_profile import router as profile_update_router
from app.routers.record_event import router as events_router
from app.routers.register_apns_token import router as devices_router
from app.routers.stats.fetch_overview import router as stats_overview_router
from app.routers.stats.list_cefr_missing import router as stats_cefr_router
from app.routers.stats.list_mistakes import router as stats_mistakes_router
from app.routers.stats.list_phrases import router as stats_phrases_router
from app.routers.webhooks.handle_apple_asn_webhook import router as apple_asn_webhook_router
from app.routers.webhooks.handle_stripe_webhook import router as stripe_webhook_router


def create_app() -> FastAPI:
    # Factory so tests can build a fresh FastAPI with isolated dependency_overrides per test.
    settings = get_settings()
    fastapi_app = FastAPI(
        title="Palkie Talkie API",
        version="0.1.0",
        lifespan=lifespan,
    )
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @fastapi_app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:  # noqa: RUF029 — FastAPI requires async route handler
        return {"status": "ok", "env": settings.app_env}

    _ = health  # keep pyright from flagging the closure-only handler as unused

    fastapi_app.include_router(conversation_start_router)
    fastapi_app.include_router(conversation_transcript_router)
    fastapi_app.include_router(conversation_end_router)
    fastapi_app.include_router(conversation_sessions_router)
    fastapi_app.include_router(stripe_webhook_router)
    fastapi_app.include_router(apple_asn_webhook_router)
    fastapi_app.include_router(entitlement_router)
    fastapi_app.include_router(personas_list_router)
    fastapi_app.include_router(personas_create_router)
    fastapi_app.include_router(personas_update_router)
    fastapi_app.include_router(personas_delete_router)
    fastapi_app.include_router(personas_like_router)
    fastapi_app.include_router(personas_unlike_router)
    fastapi_app.include_router(stats_overview_router)
    fastapi_app.include_router(stats_mistakes_router)
    fastapi_app.include_router(stats_phrases_router)
    fastapi_app.include_router(stats_cefr_router)
    fastapi_app.include_router(integrations_connect_google_router)
    fastapi_app.include_router(integrations_google_callback_router)
    fastapi_app.include_router(integrations_list_router)
    fastapi_app.include_router(integrations_apple_events_router)
    fastapi_app.include_router(integrations_outlook_router)
    fastapi_app.include_router(profile_fetch_router)
    fastapi_app.include_router(profile_update_router)
    fastapi_app.include_router(kg_router)
    fastapi_app.include_router(content_router)
    fastapi_app.include_router(devices_router)
    fastapi_app.include_router(events_router)
    fastapi_app.include_router(voices_router)
    fastapi_app.include_router(consent_fetch_router)
    fastapi_app.include_router(consent_update_router)
    return fastapi_app


app = create_app()
