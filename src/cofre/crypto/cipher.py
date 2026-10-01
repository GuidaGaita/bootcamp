"""AES-256-GCM in one column: nonce (12) || ciphertext || tag (16) (docs/04 §3.2)."""

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12
TAG_SIZE = 16


class DecryptionError(Exception):
    """Wrong key, wrong AAD or tampered data. Never carries the data itself."""


def encrypt(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def decrypt(key: bytes, blob: bytes, aad: bytes) -> bytes:
    if len(blob) < NONCE_SIZE + TAG_SIZE:
        raise DecryptionError
    try:
        return AESGCM(key).decrypt(blob[:NONCE_SIZE], blob[NONCE_SIZE:], aad)
    except InvalidTag:
        raise DecryptionError from None
