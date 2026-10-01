"""Nothing in the clear at rest, tamper detection and no leaks (RNF-01, RNF-03, RNF-04, A6)."""

import logging
from pathlib import Path

import pytest
from sqlalchemy import text

from cofre.core.logging import JsonFormatter

pytestmark = [pytest.mark.security, pytest.mark.req("RNF-01", "RNF-03", "RNF-04")]

URL = "/api/v1/credentials"
MARKERS = {
    "title": "MARCADOR-TITULO-banco",
    "password": "MARCADOR-SENHA-cofre",
    "username": "MARCADOR-USUARIO-ana",
    "url": "https://marcador-url.example/login",
    "notes": "MARCADOR-NOTAS-privadas",
}


def _create(client, **override) -> dict:
    response = client.post(URL, json={**MARKERS, **override})
    assert response.status_code == 201, response.text
    return response.json()


def _ciphertext(app, credential_id: str) -> bytes:
    with app.state.engine.connect() as connection:
        return connection.execute(
            text("SELECT ciphertext FROM credentials WHERE id = :i"), {"i": credential_id}
        ).scalar_one()


def _set_ciphertext(app, credential_id: str, value: bytes) -> None:
    with app.state.engine.begin() as connection:
        connection.execute(
            text("UPDATE credentials SET ciphertext = :c WHERE id = :i"),
            {"c": value, "i": credential_id},
        )


def test_database_file_contains_none_of_the_credential_in_the_clear(auth_client, settings):
    created = _create(auth_client)
    auth_client.patch(f"{URL}/{created['id']}", json={"notes": MARKERS["notes"] + "-2"})

    raw = Path(settings.database_url.removeprefix("sqlite:///")).read_bytes()

    for value in MARKERS.values():
        assert value.encode() not in raw
    assert b"MARCADOR" not in raw


def test_stored_value_has_nonce_ciphertext_tag_layout(app, auth_client):
    created = _create(auth_client)

    blob = _ciphertext(app, created["id"])

    assert len(blob) > 12 + 16
    with app.state.engine.connect() as connection:
        version = connection.execute(text("SELECT enc_version FROM credentials")).scalar_one()
    assert version == 1


def test_every_encryption_uses_a_new_nonce(app, auth_client):
    first = _create(auth_client)
    second = _create(auth_client)
    before = _ciphertext(app, first["id"])
    auth_client.patch(f"{URL}/{first['id']}", json={"title": MARKERS["title"]})  # same content
    after = _ciphertext(app, first["id"])

    nonces = {before[:12], after[:12], _ciphertext(app, second["id"])[:12]}

    assert len(nonces) == 3 and before != after


def test_tampered_ciphertext_fails_integrity_without_details(app, auth_client):
    created = _create(auth_client)
    blob = bytearray(_ciphertext(app, created["id"]))
    blob[20] ^= 0x01
    _set_ciphertext(app, created["id"], bytes(blob))

    response = auth_client.get(f"{URL}/{created['id']}")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "Erro interno inesperado."}
    }
    assert auth_client.get(URL).status_code == 500  # the list decrypts everything too


def test_truncated_ciphertext_fails_integrity(app, auth_client):
    created = _create(auth_client)
    _set_ciphertext(app, created["id"], b"curto")

    assert auth_client.get(f"{URL}/{created['id']}").status_code == 500


def test_ciphertext_copied_between_rows_or_users_is_rejected(app, auth_client_factory):
    ana = auth_client_factory("ana@email.com")
    bia = auth_client_factory("bia@email.com")
    ana_one, ana_two = _create(ana, title="um"), _create(ana, title="dois")
    bia_one = _create(bia, title="tres")

    _set_ciphertext(app, ana_one["id"], _ciphertext(app, ana_two["id"]))  # same user, other row
    assert ana.get(f"{URL}/{ana_one['id']}").status_code == 500

    _set_ciphertext(app, ana_two["id"], _ciphertext(app, bia_one["id"]))  # other user, other DEK
    assert ana.get(f"{URL}/{ana_two['id']}").status_code == 500
    assert bia.get(f"{URL}/{bia_one['id']}").status_code == 200


def test_secrets_never_reach_logs_or_non_get_responses(auth_client, caplog, capsys):
    with caplog.at_level(logging.DEBUG):
        created = auth_client.post(URL, json=MARKERS)
        listed = auth_client.get(URL, params={"q": "marcador"})
        patched = auth_client.patch(
            f"{URL}/{created.json()['id']}", json={"password": "MARCADOR-NOVA"}
        )
        fetched = auth_client.get(f"{URL}/{created.json()['id']}")
        auth_client.get(f"{URL}/nao-e-uuid")  # 422

    for response in (created, listed, patched):
        assert "MARCADOR-SENHA" not in response.text and "MARCADOR-NOVA" not in response.text
    assert fetched.json()["password"] == "MARCADOR-NOVA"  # RF-11 is the only place it appears
    emitted = "\n".join(JsonFormatter().format(r) for r in caplog.records)
    captured = capsys.readouterr()
    for output in (
        caplog.text,
        emitted,
        repr([vars(r) for r in caplog.records]),
        captured.out,
        captured.err,
    ):
        assert "MARCADOR" not in output


def test_integrity_failure_is_logged_with_the_id_only(app, auth_client, caplog):
    created = _create(auth_client)
    _set_ciphertext(app, created["id"], b"x" * 40)

    with caplog.at_level(logging.INFO, logger="cofre"):
        auth_client.get(f"{URL}/{created['id']}")

    (record,) = [
        r for r in caplog.records if getattr(r, "event", None) == "credential_integrity_failure"
    ]
    assert record.levelno == logging.ERROR and record.credential_id == created["id"]
    assert "MARCADOR" not in JsonFormatter().format(record) and "MARCADOR" not in caplog.text
