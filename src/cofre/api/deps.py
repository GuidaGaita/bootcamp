"""FastAPI dependencies that read per-application state."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.services.health import HealthService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_clock(request: Request) -> Clock:
    return request.app.state.clock


def get_db(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_health_service(request: Request) -> HealthService:
    return HealthService(request.app.state.engine)
