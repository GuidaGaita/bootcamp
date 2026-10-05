"""Key-encryption-key derivation (docs/04 §3.1)."""

from argon2.low_level import Type, hash_secret_raw


def derive_kek(
    password: str, salt: bytes, memory_kib: int, time_cost: int, parallelism: int
) -> bytes:
    return hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_kib,
        parallelism=parallelism,
        hash_len=32,
        type=Type.ID,
    )
