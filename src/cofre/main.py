"""Application factory (FR-017, FR-022)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import cofre
from cofre.api.errors import register_error_handlers
from cofre.api.middleware import RequestContextMiddleware
from cofre.api.routers import accounts, credentials, health, sessions
from cofre.core.clock import Clock, SystemClock
from cofre.core.config import Settings, load_settings
from cofre.core.logging import configure_logging, log_event
from cofre.crypto import hashing
from cofre.repositories.database import build_engine, build_session_factory, init_schema


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    """Build an independent application; reads the environment only when ``settings`` is None."""
    if settings is None:
        settings = load_settings()
    if clock is None:
        clock = SystemClock()
    configure_logging()
    hashing.dummy_hash(*settings.argon2_cost)  # built now, so no login pays for it (A3)

    engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        try:
            init_schema(engine, settings.database_url)
        except Exception as exc:  # the app must start without a database
            log_event(
                settings.log_level,
                clock,
                logging.ERROR,
                "database_init_failed",
                error_type=type(exc).__name__,
            )
        yield
        engine.dispose()

    app = FastAPI(
        title="Cofre API",
        version=cofre.__version__,
        summary="API REST multiusuário de gerenciamento de senhas.",
        description=(
            "Erros seguem o formato padronizado de docs/03 §6.3. Toda resposta traz "
            "`X-Request-ID`, e as respostas sob `/api/v1` trazem `Cache-Control: no-store`."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.clock = clock
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(accounts.router)
    app.include_router(sessions.router)
    app.include_router(credentials.router)
    app.add_middleware(RequestContextMiddleware)
    return app
