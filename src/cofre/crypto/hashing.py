"""Master-password normalization and Argon2id verification hash (docs/04 §3.1)."""

import unicodedata
from functools import cache

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


def normalize_password(password: str) -> str:
    """NFKC, applied before any validation, hash or key derivation (RN-02)."""
    return unicodedata.normalize("NFKC", password)


def hash_password(password: str, memory_kib: int, time_cost: int, parallelism: int) -> str:
    hasher = PasswordHasher(
        time_cost=time_cost,
        memory_cost=memory_kib,
        parallelism=parallelism,
        hash_len=32,
        salt_len=16,
        type=Type.ID,
    )
    return hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Constant-time check; the cost parameters are read from the PHC string."""
    try:
        return PasswordHasher().verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


@cache
def dummy_hash(memory_kib: int, time_cost: int, parallelism: int) -> str:
    """Hash checked when the e-mail does not exist, to equalize response time (docs/04 A3)."""
    return hash_password("cofre-dummy-password", memory_kib, time_cost, parallelism)
