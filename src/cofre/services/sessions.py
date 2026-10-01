"""Login, request authentication and logout (docs/04 §4)."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from cofre.core.clock import Clock
from cofre.core.config import Settings
from cofre.core.errors import CofreError, InvalidCredentialsError, UnauthenticatedError
from cofre.crypto import cipher, hashing, kdf, keys, tokens
from cofre.repositories.models import UserSession
from cofre.repositories.sessions import SessionRepository
from cofre.repositories.users import UserRepository
from cofre.services.throttle import ThrottleService
from cofre.services.validation import normalize_email


@dataclass(frozen=True)
class AuthContext:
    """Who is calling. The DEK lives only for the duration of the request."""

    user_id: str
    session_id: str
    dek: bytes = field(repr=False)


class SessionService:
    def __init__(self, db: Session, clock: Clock, settings: Settings) -> None:
        self._db = db
        self._clock = clock
        self._settings = settings
        self._users = UserRepository(db)
        self._sessions = SessionRepository(db)
        self._throttle = ThrottleService(db, clock, settings)

    def login(self, email: str, password: str) -> tuple[str, datetime]:
        email = normalize_email(email)
        password = hashing.normalize_password(password)
        attempt = self._throttle.begin_attempt(email)  # counted before the check (RN-14)

        user = self._users.get_by_email(email)
        s = self._settings
        stored = user.password_hash if user else hashing.dummy_hash(*s.argon2_cost)
        verified = hashing.verify_password(stored, password)  # always runs: equal timing (A3)
        if user is None or not verified:
            self._throttle.register_failure(email, attempt)
            raise InvalidCredentialsError

        params = user.kdf_params
        kek = kdf.derive_kek(
            password,
            user.kdf_salt,
            params["memory_kib"],
            params["time_cost"],
            params["parallelism"],
        )
        try:
            dek = keys.unwrap_dek(kek, user.wrapped_dek, user.id)
        except cipher.DecryptionError:
            raise CofreError from None

        token = tokens.new_token()
        raw = tokens.decode_token(token)
        session_id = str(uuid.uuid4())
        now = self._clock.now()
        expires_at = now + timedelta(minutes=s.session_ttl_minutes)
        self._throttle.reset(email)
        self._sessions.delete_expired_for_user(user.id, now)
        self._sessions.add(
            UserSession(
                id=session_id,
                user_id=user.id,
                token_hash=tokens.sha256_hex(raw),
                session_wrapped_dek=keys.wrap_session_dek(keys.session_key(raw), dek, session_id),
                created_at=now,
                expires_at=expires_at,
            )
        )
        self._db.commit()
        return token, expires_at

    def resolve(self, token: str) -> AuthContext:
        raw = tokens.decode_token(token)
        if raw is None:
            raise UnauthenticatedError
        session = self._sessions.get_by_token_hash(tokens.sha256_hex(raw))
        if session is None:
            raise UnauthenticatedError
        if session.expires_at <= self._clock.now():
            self._sessions.delete(session.id, session.user_id)
            self._db.commit()
            raise UnauthenticatedError
        try:
            dek = keys.unwrap_session_dek(
                keys.session_key(raw), session.session_wrapped_dek, session.id
            )
        except cipher.DecryptionError:
            raise UnauthenticatedError from None
        return AuthContext(user_id=session.user_id, session_id=session.id, dek=dek)

    def logout(self, context: AuthContext) -> None:
        self._sessions.delete(context.session_id, context.user_id)
        self._db.commit()
