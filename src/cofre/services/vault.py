"""Credential vault: encrypted CRUD, in-memory search and pagination (RF-08 to RF-13)."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import DataIntegrityError, NotFoundError, VaultLimitReachedError
from cofre.crypto import cipher, keys
from cofre.repositories.credentials import CredentialRepository
from cofre.repositories.models import Credential
from cofre.services.sessions import AuthContext

ENC_VERSION = 1
FIELDS = ("title", "username", "password", "url", "notes")


@dataclass(frozen=True)
class CredentialData:
    id: str
    title: str
    username: str | None
    url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    password: str = field(repr=False)


class VaultService:
    def __init__(self, db: Session, clock: Clock, settings: Settings) -> None:
        self._db = db
        self._clock = clock
        self._settings = settings
        self._repo = CredentialRepository(db)

    @staticmethod
    def _seal(context: AuthContext, row_id: str, version: int, content: dict[str, Any]) -> bytes:
        plaintext = json.dumps({name: content.get(name) for name in FIELDS}).encode("utf-8")
        return cipher.encrypt(
            context.dek, plaintext, keys.credential_aad(context.user_id, row_id, version)
        )

    @staticmethod
    def _open(context: AuthContext, row: Credential) -> CredentialData:
        try:
            plaintext = cipher.decrypt(
                context.dek,
                row.ciphertext,
                keys.credential_aad(context.user_id, row.id, row.enc_version),
            )
            content = json.loads(plaintext)
        except (cipher.DecryptionError, ValueError):
            raise DataIntegrityError from None
        return CredentialData(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            **{name: content.get(name) for name in FIELDS},
        )

    def _row(self, context: AuthContext, credential_id: str) -> Credential:
        row = self._repo.get(credential_id, context.user_id)
        if row is None:
            raise NotFoundError
        return row

    def create(self, context: AuthContext, content: dict[str, Any]) -> CredentialData:
        if self._repo.count(context.user_id) >= self._settings.max_credentials_per_user:
            raise VaultLimitReachedError
        now = self._clock.now()
        row = Credential(
            id=str(uuid.uuid4()),
            user_id=context.user_id,
            enc_version=ENC_VERSION,
            created_at=now,
            updated_at=now,
        )
        row.ciphertext = self._seal(context, row.id, row.enc_version, content)
        self._repo.add(row)
        self._db.commit()
        return self._open(context, row)

    def get(self, context: AuthContext, credential_id: str) -> CredentialData:
        return self._open(context, self._row(context, credential_id))

    def list(
        self, context: AuthContext, query: str | None, limit: int, offset: int
    ) -> tuple[list[CredentialData], int]:
        """Everything is encrypted, so filtering and sorting happen after decrypting (ADR-0010)."""
        items = [self._open(context, row) for row in self._repo.list_for_user(context.user_id)]
        if query:
            needle = query.casefold()
            items = [
                item
                for item in items
                if any(
                    needle in (value or "").casefold()
                    for value in (item.title, item.username, item.url)
                )
            ]
        items.sort(key=lambda item: (item.title.casefold(), item.id))
        return items[offset : offset + limit], len(items)

    def update(
        self, context: AuthContext, credential_id: str, changes: dict[str, Any]
    ) -> CredentialData:
        row = self._row(context, credential_id)
        current = self._open(context, row)
        content = {name: getattr(current, name) for name in FIELDS}
        content.update(changes)
        row.ciphertext = self._seal(context, row.id, row.enc_version, content)
        row.updated_at = self._clock.now()
        self._db.commit()
        return self._open(context, row)

    def delete(self, context: AuthContext, credential_id: str) -> None:
        self._repo.delete(self._row(context, credential_id))
        self._db.commit()
