from datetime import datetime

import pytest
from sqlalchemy import text

from cofre.crypto.tokens import new_token
from tests.support.auth import bearer, login, register

pytestmark = [pytest.mark.api]

EMAIL = "ana@email.com"


def _me(client, token: str | None = None, headers: dict | None = None):
    return client.get("/api/v1/accounts/me", headers=headers or (bearer(token) if token else {}))


def _fail(client, email: str = EMAIL, times: int = 1):
    return [login(client, email, "senha-errada-qualquer").status_code for _ in range(times)]


@pytest.fixture
def user(client):
    assert register(client, EMAIL).status_code == 201


@pytest.mark.req("RF-03", "RN-05", "RNF-06")
def test_login_returns_token_valid_for_30_minutes(client, clock, user):
    response = login(client, EMAIL)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"token", "expires_at"}
    assert len(body["token"]) == 43
    assert datetime.fromisoformat(body["expires_at"]) == clock.now().replace(minute=30)
    assert _me(client, body["token"]).status_code == 200


@pytest.mark.req("RN-04")
def test_wrong_password_and_unknown_email_look_identical(client, user):
    wrong = login(client, EMAIL, "senha-errada-qualquer")
    unknown = login(client, "ninguem@email.com", "senha-errada-qualquer")

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.req("RF-03", "RN-04")
def test_login_normalizes_the_email(client, user):
    assert login(client, "  ANA@Email.com ").status_code == 201


@pytest.mark.req("RF-03")
def test_login_validates_structure_only(client, user):
    assert client.post("/api/v1/sessions", json={"email": EMAIL}).status_code == 422
    too_long = login(client, EMAIL, "x" * 1025)
    assert too_long.status_code == 422
    assert login(client, EMAIL, "curta").status_code == 401


@pytest.mark.req("RN-14", "RNF-07")
def test_five_failures_block_login_for_15_minutes(client, clock, user):
    assert _fail(client, times=5) == [401] * 5

    blocked = login(client, EMAIL)  # even with the right password
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"
    assert blocked.headers["Retry-After"] == "900"

    clock.advance(minutes=14)
    assert login(client, EMAIL).status_code == 429
    clock.advance(minutes=1)
    assert login(client, EMAIL).status_code == 201


@pytest.mark.req("RN-04", "RN-14")
def test_unknown_email_is_blocked_exactly_like_a_registered_one(client, user):
    assert _fail(client, "ninguem@email.com", 5) == [401] * 5
    assert _fail(client, EMAIL, 5) == [401] * 5

    unknown = login(client, "ninguem@email.com")
    known = login(client, EMAIL)

    assert unknown.status_code == known.status_code == 429
    assert unknown.json() == known.json()
    assert unknown.headers["Retry-After"] == known.headers["Retry-After"]


@pytest.mark.req("RN-14")
def test_success_resets_the_failure_counter(client, user):
    for _ in range(3):
        assert _fail(client, times=4) == [401] * 4
        assert login(client, EMAIL).status_code == 201


@pytest.mark.req("RN-14")
def test_block_is_per_email(client, user):
    assert register(client, "bia@email.com").status_code == 201
    _fail(client, times=5)

    assert login(client, "bia@email.com").status_code == 201


@pytest.mark.req("RN-05")
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer abc"},
        {"Authorization": "Bearer " + "a" * 42},
        {"Authorization": "Bearer " + "a" * 44},
        {"Authorization": "Bearer " + "!" * 43},
        {"Authorization": "Basic " + "a" * 43},
        {"Authorization": "bearer"},
    ],
    ids=["none", "empty", "short", "42", "44", "alphabet", "scheme", "lowercase-empty"],
)
def test_invalid_authorization_header_returns_401(client, user, headers):
    response = _me(client, headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.req("RN-05")
def test_well_formed_unknown_token_returns_401(client, user):
    assert _me(client, new_token()).status_code == 401


@pytest.mark.req("RN-05", "RNF-06")
def test_session_expires_after_30_minutes(client, clock, user):
    token = login(client, EMAIL).json()["token"]

    clock.advance(minutes=29)
    assert _me(client, token).status_code == 200
    clock.advance(minutes=2)

    assert _me(client, token).status_code == 401


@pytest.mark.req("RF-04")
def test_logout_invalidates_only_the_current_token(client, user):
    first = login(client, EMAIL).json()["token"]
    second = login(client, EMAIL).json()["token"]

    response = client.delete("/api/v1/sessions/current", headers=bearer(first))

    assert response.status_code == 204
    assert response.content == b""
    assert _me(client, first).status_code == 401
    assert _me(client, second).status_code == 200
    assert client.delete("/api/v1/sessions/current", headers=bearer(first)).status_code == 401


@pytest.mark.req("RF-04")
def test_logout_requires_authentication(client):
    assert client.delete("/api/v1/sessions/current").status_code == 401


@pytest.mark.req("RNF-06", "RNF-01")
def test_server_stores_only_a_hash_of_the_token(client, app, user):
    token = login(client, EMAIL).json()["token"]

    with app.state.engine.connect() as connection:
        row = connection.execute(text("SELECT token_hash, session_wrapped_dek FROM sessions")).one()

    assert len(row.token_hash) == 64 and token not in row.token_hash
    assert token.encode() not in row.session_wrapped_dek
    assert len(row.session_wrapped_dek) == 12 + 32 + 16


@pytest.mark.req("RN-05")
def test_login_removes_the_users_expired_sessions(client, clock, app, user):
    login(client, EMAIL)
    clock.advance(minutes=31)

    login(client, EMAIL)

    with app.state.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM sessions")).scalar_one() == 1
