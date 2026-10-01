import base64

import pytest

from cofre.crypto import cipher, hashing, kdf, keys, tokens

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-01", "RNF-02", "RNF-05", "RNF-06")]

COST = (1024, 1, 1)  # memory KiB, time, parallelism: reduced, tests only


def test_normalize_password_applies_nfkc():
    assert hashing.normalize_password("é") == "é"
    assert hashing.normalize_password("Ａ") == "A"


def test_password_hash_verifies_right_and_wrong_password():
    stored = hashing.hash_password("correct horse", *COST)

    assert stored.startswith("$argon2id$")
    assert hashing.verify_password(stored, "correct horse")
    assert not hashing.verify_password(stored, "wrong")
    assert "correct horse" not in stored


def test_verify_rejects_garbage_hash():
    assert not hashing.verify_password("not-a-hash", "x")


def test_dummy_hash_is_cached_per_parameters():
    assert hashing.dummy_hash(*COST) is hashing.dummy_hash(*COST)
    assert hashing.dummy_hash(*COST) != hashing.dummy_hash(2048, 1, 1)


def test_kek_depends_on_password_and_salt():
    salt = b"s" * 16
    kek = kdf.derive_kek("pw", salt, *COST)

    assert len(kek) == 32
    assert kek == kdf.derive_kek("pw", salt, *COST)
    assert kek != kdf.derive_kek("pw", b"t" * 16, *COST)
    assert kek != kdf.derive_kek("pw2", salt, *COST)


def test_cipher_round_trip_uses_nonce_ciphertext_tag_layout():
    key = keys.new_dek()

    blob = cipher.encrypt(key, b"secret", b"aad")

    assert len(blob) == 12 + len(b"secret") + 16
    assert b"secret" not in blob
    assert cipher.decrypt(key, blob, b"aad") == b"secret"


def test_cipher_uses_a_new_nonce_every_time():
    key = keys.new_dek()

    nonces = {cipher.encrypt(key, b"x", b"a")[:12] for _ in range(200)}

    assert len(nonces) == 200


@pytest.mark.parametrize("tamper", ["aad", "key", "bit", "short", "swap"])
def test_cipher_rejects_tampering(tamper):
    key, aad = keys.new_dek(), b"aad"
    blob = cipher.encrypt(key, b"secret", aad)
    other = cipher.encrypt(key, b"other!", b"other")
    if tamper == "aad":
        args = (key, blob, b"different")
    elif tamper == "key":
        args = (keys.new_dek(), blob, aad)
    elif tamper == "bit":
        args = (key, blob[:-1] + bytes([blob[-1] ^ 1]), aad)
    elif tamper == "short":
        args = (key, blob[:27], aad)
    else:
        args = (key, other, aad)

    with pytest.raises(cipher.DecryptionError):
        cipher.decrypt(*args)


def test_dek_wrap_is_bound_to_the_user():
    kek, dek = keys.new_dek(), keys.new_dek()

    wrapped = keys.wrap_dek(kek, dek, "user-1")

    assert keys.unwrap_dek(kek, wrapped, "user-1") == dek
    with pytest.raises(cipher.DecryptionError):
        keys.unwrap_dek(kek, wrapped, "user-2")


def test_session_key_is_deterministic_and_wraps_dek_per_session():
    raw = b"t" * 32
    dek = keys.new_dek()

    key = keys.session_key(raw)
    wrapped = keys.wrap_session_dek(key, dek, "session-1")

    assert key == keys.session_key(raw) and len(key) == 32
    assert key != keys.session_key(b"u" * 32)
    assert keys.unwrap_session_dek(key, wrapped, "session-1") == dek
    with pytest.raises(cipher.DecryptionError):
        keys.unwrap_session_dek(key, wrapped, "session-2")


def test_credential_aad_binds_user_credential_and_version():
    assert keys.credential_aad("u", "c", 1) == b"cofre:credential:v1:u:c"
    assert keys.credential_aad("u", "c", 1) != keys.credential_aad("v", "c", 1)


def test_new_token_is_43_chars_of_32_bytes():
    token = tokens.new_token()

    assert len(token) == 43
    assert len(tokens.decode_token(token)) == 32
    assert tokens.new_token() != token


@pytest.mark.parametrize(
    "bad",
    ["", "abc", "a" * 42, "a" * 44, "a" * 42 + "=", "a" * 42 + "!", "é" * 43, " " + "a" * 42],
)
def test_decode_token_rejects_malformed_values(bad):
    assert tokens.decode_token(bad) is None


def test_decode_token_rejects_non_canonical_encoding():
    raw = b"\x00" * 32
    canonical = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    non_canonical = canonical[:-1] + "B"

    assert tokens.decode_token(canonical) == raw
    assert tokens.decode_token(non_canonical) is None


def test_hashes_are_sha256_hex():
    assert tokens.sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
