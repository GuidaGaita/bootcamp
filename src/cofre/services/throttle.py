"""Failed-attempt control shared by login and master-password checks (RN-14, RN-16)."""

import math
from datetime import timedelta

from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import TooManyAttemptsError
from cofre.crypto.tokens import sha256_hex
from cofre.repositories.login_throttles import LoginThrottleRepository
from cofre.repositories.models import LoginThrottle


class ThrottleService:
    """Keyed by the hash of the normalized e-mail, so unknown e-mails are counted too."""

    def __init__(self, db: Session, clock: Clock, settings: Settings) -> None:
        self._repo = LoginThrottleRepository(db)
        self._db = db
        self._clock = clock
        self._settings = settings

    @staticmethod
    def _key(email: str) -> str:
        return sha256_hex(email.encode("utf-8"))

    def ensure_not_locked(self, email: str) -> None:
        row = self._repo.get(self._key(email))
        now = self._clock.now()
        if row is not None and row.locked_until is not None and row.locked_until > now:
            raise TooManyAttemptsError(math.ceil((row.locked_until - now).total_seconds()))

    def register_failure(self, email: str) -> bool:
        """Count a failure and commit; returns True when this failure reached the limit."""
        key, now = self._key(email), self._clock.now()
        row = self._repo.get(key)
        if row is None:
            row = LoginThrottle(email_hash=key, failed_count=0, locked_until=None, updated_at=now)
            self._repo.add(row)
        row.failed_count += 1
        row.updated_at = now
        reached = row.failed_count >= self._settings.login_max_attempts
        if reached:
            row.failed_count = 0
            row.locked_until = now + timedelta(minutes=self._settings.login_lock_minutes)
        self._db.commit()
        return reached

    def reset(self, email: str) -> None:
        """Forget the failures; the caller commits."""
        self._repo.delete(self._key(email))
