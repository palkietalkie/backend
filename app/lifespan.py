"""FastAPI startup/shutdown handler. `lifespan` is the framework's official term (replaces the deprecated `@app.on_event("startup")` decorators) — it's an async context manager passed to `FastAPI(lifespan=…)` where code before `yield` runs at startup and code after runs at shutdown."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import stripe
from fastapi import FastAPI
from neo4j.exceptions import GqlError

from app.audio_retention.prune_expired_audio import run_prune_expired_audio_scheduler
from app.config import get_settings
from app.daily_content.run_daily_content_scheduler import run_daily_content_scheduler
from app.services.neo4j.close_neo4j_driver import close_neo4j_driver
from app.services.neo4j.get_neo4j_driver import get_neo4j_driver


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key

    # Warm Neo4j driver if config looks real (not the bolt://localhost default)
    if settings.neo4j_uri and "localhost" not in settings.neo4j_uri:
        try:
            get_neo4j_driver()
        except GqlError:
            logging.exception("neo4j driver init failed; continuing without it")

    daily_content_task = asyncio.create_task(run_daily_content_scheduler())
    audio_prune_task = asyncio.create_task(run_prune_expired_audio_scheduler())

    try:
        yield
    finally:
        for task in (daily_content_task, audio_prune_task):
            task.cancel()
        for task in (daily_content_task, audio_prune_task):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await close_neo4j_driver()
