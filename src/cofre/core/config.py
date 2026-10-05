"""Application settings read from ``COFRE_*`` environment variables (research R8)."""

from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_core import ErrorDetails
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ENV_PREFIX = "COFRE_"

# OWASP minimums for Argon2id (docs/04 §2); only COFRE_ENV=test may go below them.
ARGON2_MIN_MEMORY_KIB = 19456
ARGON2_MIN_TIME_COST = 2

PositiveInt = Annotated[int, Field(ge=1)]


class ConfigurationError(Exception):
    """Invalid configuration; the message names variables and reasons, never values (FR-019)."""


class Settings(BaseSettings):
    """Immutable configuration (docs/08 §3, data-model.md *Settings*)."""

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, frozen=True, extra="ignore")

    env: Literal["production", "development", "test"] = "production"
    database_url: str = "sqlite:///./data/cofre.db"
    session_ttl_minutes: PositiveInt = 30
    login_max_attempts: PositiveInt = 5
    login_lock_minutes: PositiveInt = 15
    max_credentials_per_user: PositiveInt = 1000
    argon2_memory_kib: PositiveInt = ARGON2_MIN_MEMORY_KIB
    argon2_time_cost: PositiveInt = ARGON2_MIN_TIME_COST
    argon2_parallelism: PositiveInt = 1
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @property
    def argon2_cost(self) -> tuple[int, int, int]:
        """Memory (KiB), iterations and parallelism, in the order the crypto layer takes them."""
        return self.argon2_memory_kib, self.argon2_time_cost, self.argon2_parallelism

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("database_url")
    @classmethod
    def _require_sqlite(cls, value: str) -> str:
        try:
            backend = make_url(value).get_backend_name()
        except (ArgumentError, ValueError):
            raise ValueError("URL de banco inválida") from None
        if backend != "sqlite":
            raise ValueError("backend de banco não suportado; use sqlite")
        return value

    @model_validator(mode="after")
    def _require_argon2_minimums(self) -> Self:
        if self.env == "test":
            return self
        weak = []
        if self.argon2_memory_kib < ARGON2_MIN_MEMORY_KIB:
            weak.append(f"{ENV_PREFIX}ARGON2_MEMORY_KIB")
        if self.argon2_time_cost < ARGON2_MIN_TIME_COST:
            weak.append(f"{ENV_PREFIX}ARGON2_TIME_COST")
        if weak:
            raise ValueError(
                f"{', '.join(weak)} abaixo do mínimo permitido fora de {ENV_PREFIX}ENV=test"
            )
        return self


_REASONS = {
    "literal_error": "valor não permitido",
    "greater_than_equal": "abaixo do mínimo permitido",
    "int_parsing": "não é um número inteiro",
    "int_type": "não é um número inteiro",
    "int_from_float": "não é um número inteiro",
}


def _describe(error: ErrorDetails) -> str:
    if error["type"] == "value_error":
        reason = str(error["ctx"]["error"])
    else:
        reason = _REASONS.get(error["type"], "valor inválido")
    if not error["loc"]:
        return reason
    return f"{ENV_PREFIX}{str(error['loc'][0]).upper()} {reason}"


def configuration_error(exc: ValidationError) -> ConfigurationError:
    """Build a message from locations and error types only; ``input`` is never used."""
    problems = "; ".join(_describe(error) for error in exc.errors())
    return ConfigurationError(f"Configuração inválida: {problems}.")


def load_settings() -> Settings:
    """Read the environment, translating validation failures into ``ConfigurationError``."""
    try:
        return Settings()
    except ValidationError as exc:
        raise configuration_error(exc) from None
