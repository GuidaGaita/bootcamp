from sqlalchemy import select, update
from sqlalchemy.orm import Session

from cofre.repositories.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, user: User) -> None:
        self._db.add(user)
        self._db.flush()

    def get_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: str) -> User | None:
        return self._db.get(User, user_id)

    def lock(self, user_id: str) -> None:
        """No-op UPDATE: takes the database write lock for the rest of the transaction."""
        self._db.execute(update(User).where(User.id == user_id).values(updated_at=User.updated_at))

    def delete(self, user: User) -> None:
        self._db.delete(user)
