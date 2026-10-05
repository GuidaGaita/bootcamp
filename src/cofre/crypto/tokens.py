"""Opaque session tokens: 32 random bytes in unpadded base64url (docs/04 §3.1)."""

import base64
import hashlib
import re
import secrets

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}", re.ASCII)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def decode_token(token: str) -> bytes | None:
    """The 32 raw bytes, or ``None`` unless ``token`` is exactly the canonical encoding."""
    if not _TOKEN_PATTERN.fullmatch(token):
        return None
    raw = base64.urlsafe_b64decode(token + "=")
    if len(raw) != 32 or base64.urlsafe_b64encode(raw).decode().rstrip("=") != token:
        return None
    return raw


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
