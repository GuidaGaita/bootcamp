from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from cofre.repositories.models import UserSession


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, session: UserSession) -> None:
        self._db.add(session)

    def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        return self._db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))

    def delete(self, session_id: str, user_id: str) -> None:
        self._db.execute(
            delete(UserSession).where(UserSession.id == session_id, UserSession.user_id == user_id)
        )

    def delete_for_user(self, user_id: str) -> None:
        self._db.execute(delete(UserSession).where(UserSession.user_id == user_id))

    def delete_expired_for_user(self, user_id: str, now: datetime) -> None:
        self._db.execute(
            delete(UserSession).where(UserSession.user_id == user_id, UserSession.expires_at <= now)
        )
