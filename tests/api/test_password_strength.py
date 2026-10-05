import pytest

pytestmark = [pytest.mark.api, pytest.mark.req("RF-15", "RN-11")]

URL = "/api/v1/passwords/strength"


def _post(client, password):
    return client.post(URL, json={"password": password})


def test_response_has_the_contract_fields_without_authentication(client):
    response = _post(client, "Tr0ub4dor&3")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"score", "weak", "crack_time_seconds", "crack_time_display", "suggestions"}
    assert body["score"] == 3 and body["weak"] is False
    assert isinstance(body["crack_time_seconds"], float) and body["crack_time_display"]
    assert response.headers["Cache-Control"] == "no-store"
    assert "Tr0ub4dor&3" not in response.text


def test_a_weak_password_is_flagged_with_suggestions_in_portuguese(client):
    body = _post(client, "senha").json()

    assert body["weak"] is True and body["score"] <= 2
    assert "Use pelo menos 12 caracteres." in body["suggestions"]


def test_a_common_password_scores_zero(client):
    body = _post(client, "123456").json()

    assert body["score"] == 0 and "Essa senha é muito comum." in body["suggestions"]


@pytest.mark.parametrize(("size", "status"), [(0, 422), (1, 200), (1024, 200), (1025, 422)])
def test_length_boundaries(client, size, status):
    response = _post(client, "x" * size)

    assert response.status_code == status
    if status == 422:
        assert response.json()["error"]["details"][0]["field"] == "password"
        assert "xxxx" not in response.text


def test_the_longest_password_still_returns_a_finite_number(client):
    body = _post(client, "".join(chr(0x4E00 + i) for i in range(1024))).json()

    assert body["crack_time_seconds"] <= 1e300 and body["crack_time_display"] == "séculos"
    assert body["score"] == 4


def test_password_is_required(client):
    response = client.post(URL, json={})

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"field": "password", "issue": "Campo obrigatório."}
    ]
