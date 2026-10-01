import json

import pytest
from sqlalchemy import text

from cofre.crypto import kdf, keys
from tests.support.auth import VALID_PASSWORD, bearer, login, register

pytestmark = [pytest.mark.api]

NEW_PASSWORD = "outra-senha-mestra-456"
WRONG = "senha-atual-errada-999"


def _me(client, token: str):
    return client.get("/api/v1/accounts/me", headers=bearer(token))


def _change(client, token: str, current: str = VALID_PASSWORD, new: str = NEW_PASSWORD):
    return client.put(
        "/api/v1/accounts/me/master-password",
        json={"current_master_password": current, "new_master_password": new},
        headers=bearer(token),
    )


def _delete(client, token: str, password: str = VALID_PASSWORD):
    return client.post(
        "/api/v1/accounts/me/deletion", json={"master_password": password}, headers=bearer(token)
    )


def _dek(app, email: str, password: str) -> bytes:
    with app.state.engine.connect() as connection:
        row = connection.execute(
            text("SELECT id, kdf_salt, kdf_params, wrapped_dek FROM users WHERE email = :e"),
            {"e": email},
        ).one()
    params = json.loads(row.kdf_params)
    kek = kdf.derive_kek(
        password, row.kdf_salt, params["memory_kib"], params["time_cost"], params["parallelism"]
    )
    return keys.unwrap_dek(kek, row.wrapped_dek, row.id)


def _count(app, table: str) -> int:
    with app.state.engine.connect() as connection:
        return connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()


@pytest.fixture
def session(client, make_user):
    user = make_user("ana@email.com")
    token = login(client, user.email).json()["token"]
    return user, token


@pytest.mark.req("RF-05")
def test_me_returns_id_email_and_creation_date(client, session):
    user, token = session

    response = _me(client, token)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "created_at"}
    assert body["id"] == user.id and body["email"] == user.email


@pytest.mark.req("RF-06", "RN-05")
def test_change_password_revokes_all_sessions_and_keeps_the_dek(client, app, session):
    user, token = session
    other = login(client, user.email).json()["token"]
    dek_before = _dek(app, user.email, VALID_PASSWORD)

    assert _change(client, token).status_code == 204

    assert _me(client, token).status_code == 401
    assert _me(client, other).status_code == 401
    assert login(client, user.email, VALID_PASSWORD).status_code == 401
    assert login(client, user.email, NEW_PASSWORD).status_code == 201
    assert _dek(app, user.email, NEW_PASSWORD) == dek_before


@pytest.mark.req("RF-06", "RN-02")
@pytest.mark.parametrize("new", ["curta", "x" * 129, "xx-ana@email.com-xx"])
def test_change_password_validates_the_new_password(client, session, new):
    _, token = session

    response = _change(client, token, new=new)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "new_master_password"
    assert new not in response.text
    assert _me(client, token).status_code == 200


@pytest.mark.req("RF-06", "RF-07", "RN-16")
@pytest.mark.parametrize("operation", ["change", "delete"])
def test_wrong_current_password_returns_403_and_keeps_the_session(client, session, operation):
    _, token = session

    response = (
        _change(client, token, current=WRONG)
        if operation == "change"
        else _delete(client, token, WRONG)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INVALID_MASTER_PASSWORD"
    assert WRONG not in response.text
    assert _me(client, token).status_code == 200


@pytest.mark.req("RN-16", "RNF-07")
def test_failure_that_reaches_the_limit_revokes_every_session_and_blocks_login(client, session):
    user, token = session
    other = login(client, user.email).json()["token"]
    for _ in range(4):
        assert _change(client, token, current=WRONG).status_code == 403
        assert _me(client, token).status_code == 200

    assert _change(client, token, current=WRONG).status_code == 403

    assert _me(client, token).status_code == 401
    assert _me(client, other).status_code == 401
    blocked = login(client, user.email)
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers


@pytest.mark.req("RN-16")
@pytest.mark.parametrize("operation", ["change", "delete"])
def test_blocked_email_returns_429_without_checking_the_password(client, session, operation):
    user, token = session
    for _ in range(5):
        login(client, user.email, WRONG)

    response = _change(client, token) if operation == "change" else _delete(client, token)

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"
    assert "Retry-After" in response.headers
    assert _me(client, token).status_code == 200


@pytest.mark.req("RN-16", "RN-14")
def test_successful_change_resets_the_failure_counter(client, session):
    user, token = session
    for _ in range(3):
        assert _change(client, token, current=WRONG).status_code == 403
    assert _change(client, token).status_code == 204
    new_token = login(client, user.email, NEW_PASSWORD).json()["token"]

    for _ in range(4):
        assert _change(client, new_token, current=WRONG).status_code == 403

    assert _me(client, new_token).status_code == 200


@pytest.mark.req("RF-07", "RN-12")
def test_delete_account_removes_everything_and_frees_the_email(client, app, session):
    user, token = session
    login(client, user.email)

    assert _delete(client, token).status_code == 204

    assert _me(client, token).status_code == 401
    assert login(client, user.email).status_code == 401
    assert _count(app, "users") == 0 and _count(app, "sessions") == 0
    assert register(client, user.email).status_code == 201


@pytest.mark.req("RF-07", "RN-12", "RNF-03")
def test_delete_account_does_not_touch_other_users(client, app, auth_client_factory):
    victim = auth_client_factory("ana@email.com")
    bystander = auth_client_factory("bia@email.com")

    assert _delete(victim, victim.token).status_code == 204

    assert _me(bystander, bystander.token).status_code == 200
    assert _count(app, "users") == 1 and _count(app, "sessions") == 1


@pytest.mark.req("RF-05", "RF-06", "RF-07", "RN-05")
def test_account_routes_require_authentication(client):
    assert client.get("/api/v1/accounts/me").status_code == 401
    assert client.put("/api/v1/accounts/me/master-password", json={}).status_code == 401
    assert client.post("/api/v1/accounts/me/deletion", json={}).status_code == 401
