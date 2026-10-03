import pytest

from cofre.services.passwords import AMBIGUOUS

pytestmark = [pytest.mark.api, pytest.mark.req("RF-14", "RN-10")]

URL = "/api/v1/passwords/generate"


def test_defaults_without_authentication(client):
    response = client.post(URL, json={})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"password"} and len(body["password"]) == 20
    assert response.headers["Cache-Control"] == "no-store"
    assert "Authorization" not in response.request.headers


def test_a_body_is_optional_in_practice_but_must_be_json(client):
    assert (
        client.post(URL, content=b"{", headers={"Content-Type": "application/json"}).status_code
        == 422
    )


@pytest.mark.parametrize(("length", "status"), [(7, 422), (8, 200), (128, 200), (129, 422)])
def test_length_boundaries(client, length, status):
    response = client.post(URL, json={"length": length})

    assert response.status_code == status
    if status == 200:
        assert len(response.json()["password"]) == length
    else:
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert response.json()["error"]["details"][0]["field"] == "length"


@pytest.mark.parametrize("length", ["vinte", 20.5, None, True])
def test_length_must_be_an_integer(client, length):
    assert client.post(URL, json={"length": length}).status_code == 422


def test_all_sets_disabled_returns_422(client):
    response = client.post(
        URL, json={"lowercase": False, "uppercase": False, "digits": False, "symbols": False}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_selected_sets_are_respected(client):
    password = client.post(URL, json={"length": 40, "uppercase": False, "symbols": False}).json()[
        "password"
    ]

    assert any(c.islower() for c in password) and any(c.isdigit() for c in password)
    assert not any(c.isupper() for c in password)
    assert all(c.isalnum() for c in password)


def test_length_8_with_four_sets_and_exclude_ambiguous(client):
    for _ in range(30):
        password = client.post(URL, json={"length": 8, "exclude_ambiguous": True}).json()[
            "password"
        ]

        assert len(password) == 8 and not set(password) & AMBIGUOUS
        assert any(c.islower() for c in password) and any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(not c.isalnum() for c in password)


def test_two_calls_return_different_passwords(client):
    first = client.post(URL, json={}).json()["password"]
    second = client.post(URL, json={}).json()["password"]

    assert first != second
