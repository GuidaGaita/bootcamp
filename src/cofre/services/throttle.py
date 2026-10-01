"""Failed-attempt control shared by login and master-password checks (RN-14, RN-16).

The attempt is counted *before* the password is verified, with one atomic statement, so a burst
of parallel guesses cannot slip past the limit: the sixth attempt is refused whatever the others
are doing. A success erases the count.
"""

import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import TooManyAttemptsError
from cofre.crypto.tokens import sha256_hex
from cofre.repositories.login_throttles import LoginThrottleRepository

IDLE_RETENTION = timedelta(hours=24)


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

    def _refuse(self, key: str, now: datetime) -> TooManyAttemptsError:
        row = self._repo.get(key)
        remaining = (row.locked_until - now).total_seconds() if row and row.locked_until else 0
        self._db.commit()
        return TooManyAttemptsError(math.ceil(remaining))

    def begin_attempt(self, email: str) -> int:
        """Refuse if locked; otherwise count this attempt and return its number (1-based)."""
        key, now = self._key(email), self._clock.now()
        self._repo.prune(now - IDLE_RETENTION, now)
        self._repo.expire_stale_lock(key, now)
        row = self._repo.get(key)
        if row is not None and row.locked_until is not None and row.locked_until > now:
            raise self._refuse(key, now)

        count = self._repo.increment(key, now)
        if count > self._settings.login_max_attempts:
            self._repo.lock(key, now + timedelta(minutes=self._settings.login_lock_minutes))
            raise self._refuse(key, now)
        self._db.commit()
        return count

    def register_failure(self, email: str, attempt: int) -> bool:
        """Lock the e-mail if ``attempt`` reached the limit; returns True in that case."""
        if attempt < self._settings.login_max_attempts:
            return False
        now = self._clock.now()
        self._repo.lock(
            self._key(email), now + timedelta(minutes=self._settings.login_lock_minutes)
        )
        self._db.commit()
        return True

    def reset(self, email: str) -> None:
        """Forget the failures; the caller commits."""
        self._repo.delete(self._key(email))
