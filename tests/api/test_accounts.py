import pytest
from sqlalchemy import text

from tests.support.auth import VALID_PASSWORD, login, register

pytestmark = [pytest.mark.api]


@pytest.mark.req("RF-02", "RN-01")
def test_register_returns_201_with_normalized_email(client):
    response = register(client, " Ana@Email.com ")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "created_at"}
    assert body["email"] == "ana@email.com"
    assert body["created_at"].endswith("Z") or "+00:00" in body["created_at"]
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.req("RF-02", "RN-01")
def test_register_same_email_with_other_case_returns_409(client):
    assert register(client, "Ana@Email.com ").status_code == 201

    response = register(client, "ana@email.com")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.req("RF-02", "RN-01", "RN-02")
@pytest.mark.parametrize(
    ("email", "password", "field"),
    [
        ("sem-arroba", VALID_PASSWORD, "email"),
        ("a" * 251 + "@x.co", VALID_PASSWORD, "email"),
        ("ana@email.com", "x" * 11, "master_password"),
        ("ana@email.com", "x" * 129, "master_password"),
        ("ana@email.com", "xx-ANA@email.com-xx", "master_password"),
    ],
)
def test_register_rejects_invalid_input_without_echoing_it(client, email, password, field):
    response = register(client, email, password)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert [d["field"] for d in error["details"]] == [field]
    assert password not in response.text


@pytest.mark.req("RF-02", "RN-01", "RN-02")
def test_register_accepts_boundary_sizes(client):
    assert register(client, "a" * 249 + "@x.co", "x" * 12).status_code == 201
    assert register(client, "b@x.co", "y" * 128).status_code == 201


@pytest.mark.req("RF-02")
def test_register_requires_both_fields(client):
    response = client.post("/api/v1/accounts", json={"email": "ana@email.com"})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "master_password"


@pytest.mark.req("RF-03", "RN-02")
def test_accented_password_registered_precomposed_logs_in_decomposed(client):
    assert register(client, "ana@email.com", "senha-café-longa-1").status_code == 201

    assert login(client, "ana@email.com", "senha-café-longa-1").status_code == 201


@pytest.mark.req("RNF-02", "RNF-01")
def test_database_never_stores_the_master_password(client, app):
    secret = "senha-que-nao-pode-vazar-1"
    assert register(client, "ana@email.com", secret).status_code == 201

    with app.state.engine.connect() as connection:
        row = connection.execute(
            text("SELECT password_hash, kdf_salt, wrapped_dek, kdf_params FROM users")
        ).one()

    stored = b"".join(v if isinstance(v, bytes) else str(v).encode() for v in row)
    assert secret.encode() not in stored
    assert row.password_hash.startswith("$argon2id$")
    assert len(row.kdf_salt) == 16
    assert len(row.wrapped_dek) == 12 + 32 + 16


@pytest.mark.req("RF-02", "RNF-04")
@pytest.mark.parametrize(
    ("email", "password"), [("a@x.co", "x" * 1025), ("a" * 321, VALID_PASSWORD)]
)
def test_oversized_fields_are_refused_before_hashing(client, email, password):
    response = register(client, email, password)

    assert response.status_code == 422
    assert password not in response.text
