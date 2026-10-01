from sqlalchemy.orm import Session

from cofre.repositories.models import LoginThrottle


class LoginThrottleRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, email_hash: str) -> LoginThrottle | None:
        return self._db.get(LoginThrottle, email_hash)

    def add(self, throttle: LoginThrottle) -> None:
        self._db.add(throttle)

    def delete(self, email_hash: str) -> None:
        row = self._db.get(LoginThrottle, email_hash)
        if row is not None:
            self._db.delete(row)
