"""FastAPI dependencies that read per-application state."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import UnauthenticatedError
from cofre.services.accounts import AccountService
from cofre.services.health import HealthService
from cofre.services.sessions import AuthContext, SessionService
from cofre.services.vault import VaultService


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


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
AppClock = Annotated[Clock, Depends(get_clock)]


def get_health_service(request: Request) -> HealthService:
    return HealthService(request.app.state.engine)


def get_account_service(db: DbSession, clock: AppClock, settings: AppSettings) -> AccountService:
    return AccountService(db, clock, settings)


def get_session_service(db: DbSession, clock: AppClock, settings: AppSettings) -> SessionService:
    return SessionService(db, clock, settings)


def get_vault_service(db: DbSession, clock: AppClock, settings: AppSettings) -> VaultService:
    return VaultService(db, clock, settings)


def get_auth_context(
    request: Request, service: Annotated[SessionService, Depends(get_session_service)]
) -> AuthContext:
    """``Authorization: Bearer <token>``; any other shape is a 401 in the standard format."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthenticatedError
    return service.resolve(token)


CurrentUser = Annotated[AuthContext, Depends(get_auth_context)]
