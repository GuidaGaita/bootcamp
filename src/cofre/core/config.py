"""Application settings read from ``COFRE_*`` environment variables (research R8)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable configuration (docs/08 §3, data-model.md *Settings*)."""

    model_config = SettingsConfigDict(env_prefix="COFRE_", frozen=True, extra="ignore")

    env: str = "production"
    database_url: str = "sqlite:///./data/cofre.db"
    session_ttl_minutes: int = 30
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    max_credentials_per_user: int = 1000
    argon2_memory_kib: int = 19456
    argon2_time_cost: int = 2
    argon2_parallelism: int = 1
    log_level: str = "INFO"
