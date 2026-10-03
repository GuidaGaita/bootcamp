"""Every query filters by ``user_id`` (RNF-03, docs/04 §5 rule 4)."""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from cofre.repositories.models import Credential


class CredentialRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, credential: Credential) -> None:
        self._db.add(credential)

    def get(self, credential_id: str, user_id: str) -> Credential | None:
        return self._db.scalar(
            select(Credential).where(Credential.id == credential_id, Credential.user_id == user_id)
        )

    def list_for_user(self, user_id: str) -> list[Credential]:
        return list(self._db.scalars(select(Credential).where(Credential.user_id == user_id)))

    def count(self, user_id: str) -> int:
        return (
            self._db.scalar(
                select(func.count()).select_from(Credential).where(Credential.user_id == user_id)
            )
            or 0
        )

    def delete(self, credential: Credential) -> None:
        self._db.delete(credential)

    def delete_for_user(self, user_id: str) -> None:
        self._db.execute(delete(Credential).where(Credential.user_id == user_id))
