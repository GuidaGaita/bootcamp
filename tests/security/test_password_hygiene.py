"""The evaluated password is never echoed or logged; the generated one is never logged."""

import logging

import pytest

from cofre.api.schemas.passwords import StrengthRequest
from cofre.core.logging import JsonFormatter

pytestmark = [pytest.mark.security, pytest.mark.req("RNF-04", "RNF-05", "RF-14", "RF-15")]

MARKER = "MARCADOR-SENHA-avaliada-9!"


def _emitted(caplog) -> str:
    lines = (JsonFormatter().format(record) for record in caplog.records)
    return "\n".join(lines) + caplog.text + repr([vars(r) for r in caplog.records])


def test_evaluated_password_is_not_echoed_or_logged(client, caplog, capsys):
    with caplog.at_level(logging.DEBUG):
        ok = client.post("/api/v1/passwords/strength", json={"password": MARKER})
        invalid = client.post("/api/v1/passwords/strength", json={"password": MARKER * 100})

    captured = capsys.readouterr()
    assert ok.status_code == 200 and invalid.status_code == 422
    for text in (ok.text, invalid.text, _emitted(caplog), captured.out, captured.err):
        assert MARKER not in text


def test_schema_hides_the_password_in_repr():
    request = StrengthRequest(password=MARKER)

    assert MARKER not in repr(request) and MARKER not in str(request.model_dump())


def test_generated_password_is_not_logged(client, caplog, capsys):
    with caplog.at_level(logging.DEBUG):
        passwords = [
            client.post("/api/v1/passwords/generate", json={"length": 32}).json()["password"]
            for _ in range(5)
        ]

    captured = capsys.readouterr()
    for password in passwords:
        for text in (_emitted(caplog), captured.out, captured.err):
            assert password not in text
