"""DEK handling, key wrapping, session key and AAD builders (docs/04 §3.2 and §4)."""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from cofre.crypto import cipher

SESSION_KEY_INFO = b"cofre/session-key/v1"


def new_dek() -> bytes:
    return os.urandom(32)


def wrap_dek(kek: bytes, dek: bytes, user_id: str) -> bytes:
    return cipher.encrypt(kek, dek, f"cofre:dek:v1:{user_id}".encode())


def unwrap_dek(kek: bytes, wrapped: bytes, user_id: str) -> bytes:
    return cipher.decrypt(kek, wrapped, f"cofre:dek:v1:{user_id}".encode())


def session_key(token: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=SESSION_KEY_INFO).derive(
        token
    )


def wrap_session_dek(key: bytes, dek: bytes, session_id: str) -> bytes:
    return cipher.encrypt(key, dek, f"cofre:session-dek:v1:{session_id}".encode())


def unwrap_session_dek(key: bytes, wrapped: bytes, session_id: str) -> bytes:
    return cipher.decrypt(key, wrapped, f"cofre:session-dek:v1:{session_id}".encode())


def credential_aad(user_id: str, credential_id: str, enc_version: int) -> bytes:
    return f"cofre:credential:v{enc_version}:{user_id}:{credential_id}".encode()
