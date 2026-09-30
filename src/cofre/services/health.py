"""Health check service (FR-002, FR-003)."""

from enum import StrEnum

from sqlalchemy import Engine

from cofre.core.errors import ServiceUnavailableError
from cofre.repositories.database import ping


class HealthStatus(StrEnum):
    OK = "ok"


class HealthService:
    """Checks the database on every call, without caching the result."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def check(self) -> HealthStatus:
        try:
            ping(self._engine)
        except Exception as exc:
            raise ServiceUnavailableError from exc
        return HealthStatus.OK
