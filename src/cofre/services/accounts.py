"""Account lifecycle: register, read, change master password, delete (docs/04 §4)."""

import secrets
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import (
    EmailAlreadyRegisteredError,
    InvalidMasterPasswordError,
    UnauthenticatedError,
)
from cofre.crypto import hashing, kdf, keys
from cofre.repositories.models import User
from cofre.repositories.sessions import SessionRepository
from cofre.repositories.users import UserRepository
from cofre.services.sessions import AuthContext
from cofre.services.throttle import ThrottleService
from cofre.services.validation import normalize_email, validate_email, validate_master_password


class AccountService:
    def __init__(self, db: Session, clock: Clock, settings: Settings) -> None:
        self._db = db
        self._clock = clock
        self._settings = settings
        self._users = UserRepository(db)
        self._sessions = SessionRepository(db)
        self._throttle = ThrottleService(db, clock, settings)

    def _cost(self) -> tuple[int, int, int]:
        s = self._settings
        return s.argon2_memory_kib, s.argon2_time_cost, s.argon2_parallelism

    def _key_material(self, password: str, user_id: str, dek: bytes) -> dict[str, object]:
        """New hash, salt, KDF parameters and wrapped DEK for ``password``."""
        memory, time_cost, parallelism = self._cost()
        salt = secrets.token_bytes(16)
        kek = kdf.derive_kek(password, salt, memory, time_cost, parallelism)
        return {
            "password_hash": hashing.hash_password(password, memory, time_cost, parallelism),
            "kdf_salt": salt,
            "kdf_params": {
                "memory_kib": memory,
                "time_cost": time_cost,
                "parallelism": parallelism,
            },
            "wrapped_dek": keys.wrap_dek(kek, dek, user_id),
        }

    def _user(self, user_id: str) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UnauthenticatedError
        return user

    def register(self, email: str, password: str) -> User:
        email = normalize_email(email)
        validate_email(email)
        password = hashing.normalize_password(password)
        validate_master_password(password, email)
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        now = self._clock.now()
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            created_at=now,
            updated_at=now,
            **self._key_material(password, user_id, keys.new_dek()),
        )
        try:
            self._users.add(user)
            self._db.commit()
        except IntegrityError:  # concurrent registration of the same e-mail
            self._db.rollback()
            raise EmailAlreadyRegisteredError from None
        return user

    def me(self, context: AuthContext) -> User:
        return self._user(context.user_id)

    def _check_master_password(self, user: User, password: str) -> None:
        """RN-16: lock check, then verification; a failure is counted and may revoke sessions."""
        self._throttle.ensure_not_locked(user.email)
        if hashing.verify_password(user.password_hash, hashing.normalize_password(password)):
            return
        if self._throttle.register_failure(user.email):
            self._sessions.delete_for_user(user.id)
            self._db.commit()
        raise InvalidMasterPasswordError

    def change_master_password(
        self, context: AuthContext, current_password: str, new_password: str
    ) -> None:
        user = self._user(context.user_id)
        new_password = hashing.normalize_password(new_password)
        validate_master_password(new_password, user.email, field="new_master_password")
        self._check_master_password(user, current_password)

        for name, value in self._key_material(new_password, user.id, context.dek).items():
            setattr(user, name, value)
        user.updated_at = self._clock.now()
        self._sessions.delete_for_user(user.id)
        self._throttle.reset(user.email)
        self._db.commit()

    def delete(self, context: AuthContext, password: str) -> None:
        user = self._user(context.user_id)
        self._check_master_password(user, password)
        self._sessions.delete_for_user(user.id)
        self._users.delete(user)
        self._throttle.reset(user.email)
        self._db.commit()
