from sqlalchemy import select
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

    def delete(self, user: User) -> None:
        self._db.delete(user)
