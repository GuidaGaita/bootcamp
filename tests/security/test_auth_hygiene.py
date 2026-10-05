"""No password or token in logs, errors or reprs; no `random` for security (RNF-04, RNF-05)."""

import logging
import re
from pathlib import Path

import pytest

from cofre.api.schemas.accounts import ChangePasswordRequest, DeleteAccountRequest, RegisterRequest
from cofre.api.schemas.sessions import LoginRequest
from cofre.core.logging import JsonFormatter
from tests.support.auth import bearer, login, register

pytestmark = [pytest.mark.security, pytest.mark.req("RNF-04", "RNF-05")]

SECRET = "MARCADOR-SENHA-mestra-1"
NEW_SECRET = "MARCADOR-NOVA-senha-mestra-2"
SRC = Path(__file__).resolve().parents[2] / "src" / "cofre"


def test_passwords_and_tokens_never_reach_logs_or_error_bodies(client, caplog, capsys):
    bodies = []
    with caplog.at_level(logging.DEBUG):
        bodies.append(register(client, "ana@email.com", SECRET))
        bodies.append(register(client, "ana@email.com", SECRET))  # 409
        bodies.append(register(client, "bia@email.com", "curta"))  # 422
        bodies.append(login(client, "ana@email.com", "MARCADOR-ERRADA-xyz"))  # 401
        ok = login(client, "ana@email.com", SECRET)
        token = ok.json()["token"]
        bodies.append(
            client.put(
                "/api/v1/accounts/me/master-password",
                json={
                    "current_master_password": "MARCADOR-ATUAL-errada",
                    "new_master_password": NEW_SECRET,
                },
                headers=bearer(token),
            )
        )  # 403
        bodies.append(
            client.put(
                "/api/v1/accounts/me/master-password",
                json={"current_master_password": SECRET, "new_master_password": NEW_SECRET},
                headers=bearer(token),
            )
        )
        bodies.append(client.get("/api/v1/accounts/me", headers=bearer(token)))  # 401 now

    emitted = "\n".join(JsonFormatter().format(r) for r in caplog.records)
    captured = capsys.readouterr()
    for text in (
        caplog.text,
        emitted,
        repr([vars(r) for r in caplog.records]),
        captured.out,
        captured.err,
    ):
        for secret in (SECRET, NEW_SECRET, "MARCADOR-ERRADA", "MARCADOR-ATUAL", token):
            assert secret not in text
    for response in bodies:
        if response.status_code >= 400:
            for secret in (SECRET, NEW_SECRET, "MARCADOR-ERRADA", "MARCADOR-ATUAL", token):
                assert secret not in response.text


def test_request_schemas_hide_secrets_in_repr():
    objects = [
        RegisterRequest(email="a@b.co", master_password=SECRET),
        LoginRequest(email="a@b.co", master_password=SECRET),
        ChangePasswordRequest(current_master_password=SECRET, new_master_password=NEW_SECRET),
        DeleteAccountRequest(master_password=SECRET),
    ]

    for obj in objects:
        assert SECRET not in repr(obj) and NEW_SECRET not in repr(obj)
        assert SECRET not in str(obj.model_dump())


def test_the_random_module_is_never_imported():
    pattern = re.compile(r"^\s*(import random\b|from random import)", re.MULTILINE)

    offenders = [
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []
