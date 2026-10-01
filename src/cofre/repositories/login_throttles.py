from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from cofre.repositories.models import LoginThrottle


class LoginThrottleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, email_hash: str) -> LoginThrottle | None:
        statement = select(LoginThrottle).where(LoginThrottle.email_hash == email_hash)
        return self._db.scalar(statement.execution_options(populate_existing=True))

    def increment(self, email_hash: str, now: datetime) -> int:
        """Atomic upsert (one statement): concurrent attempts each get a distinct count."""
        statement = insert(LoginThrottle).values(
            email_hash=email_hash, failed_count=1, locked_until=None, updated_at=now
        )
        table = LoginThrottle.__table__
        statement = statement.on_conflict_do_update(
            index_elements=["email_hash"],
            set_={"failed_count": table.c.failed_count + 1, "updated_at": now},
        ).returning(LoginThrottle.failed_count)
        return self._db.execute(statement).scalar_one()

    def expire_stale_lock(self, email_hash: str, now: datetime) -> None:
        self._db.execute(
            update(LoginThrottle)
            .where(
                LoginThrottle.email_hash == email_hash,
                LoginThrottle.locked_until.is_not(None),
                LoginThrottle.locked_until <= now,
            )
            .values(failed_count=0, locked_until=None)
        )

    def lock(self, email_hash: str, until: datetime) -> None:
        self._db.execute(
            update(LoginThrottle)
            .where(LoginThrottle.email_hash == email_hash, LoginThrottle.locked_until.is_(None))
            .values(locked_until=until)
        )

    def prune(self, cutoff: datetime, now: datetime) -> None:
        """Drop idle rows so unknown e-mails cannot grow the table forever."""
        self._db.execute(
            delete(LoginThrottle).where(
                LoginThrottle.updated_at < cutoff,
                or_(LoginThrottle.locked_until.is_(None), LoginThrottle.locked_until <= now),
            )
        )

    def delete(self, email_hash: str) -> None:
        self._db.execute(delete(LoginThrottle).where(LoginThrottle.email_hash == email_hash))
