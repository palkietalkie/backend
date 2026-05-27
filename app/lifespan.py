import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import stripe
from fastapi import FastAPI
from neo4j.exceptions import Neo4jError

from app.config import get_settings
from app.services.neo4j.close_driver import close_driver
from app.services.neo4j.get_driver import get_driver


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key

    # Warm Neo4j driver if config looks real (not the bolt://localhost default)
    if settings.neo4j_uri and "localhost" not in settings.neo4j_uri:
        try:
            get_driver()
        except Neo4jError:
            logging.exception("neo4j driver init failed; continuing without it")

    yield

    await close_driver()
