from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from cofre.main import create_app
from tests.conftest import make_settings
from tests.support.auth import VALID_PASSWORD, bearer, login, register
from tests.support.clock import FakeClock

pytestmark = [pytest.mark.api]

URL = "/api/v1/credentials"
FULL = {
    "title": "Banco",
    "password": "s3nh@-do-banco",
    "username": "ana",
    "url": "https://banco.com",
    "notes": "nota",
}


def _create(client, **override):
    return client.post(URL, json={**FULL, **override})


def _ids(response) -> list[str]:
    return [item["title"] for item in response.json()["items"]]


@pytest.fixture
def small_vault(tmp_path):
    """A client whose vault holds at most 3 credentials."""
    app = create_app(make_settings(tmp_path, max_credentials_per_user=3), FakeClock())
    with TestClient(app) as client:
        register(client, "ana@email.com")
        token = login(client, "ana@email.com").json()["token"]
        client.headers.update(bearer(token))
        yield client


@pytest.mark.req("RF-08", "RN-06", "RNF-04")
def test_create_returns_201_without_the_password(auth_client):
    response = _create(auth_client)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "title", "username", "url", "notes", "created_at", "updated_at"}
    assert body["title"] == "Banco" and body["username"] == "ana"
    assert "password" not in body and FULL["password"] not in response.text
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.req("RF-08", "RN-06")
def test_optional_fields_default_to_null_and_titles_may_repeat(auth_client):
    first = auth_client.post(URL, json={"title": "Só título", "password": "x"})
    second = auth_client.post(URL, json={"title": "Só título", "password": "y"})

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert (first.json()["username"], first.json()["url"], first.json()["notes"]) == (None,) * 3


@pytest.mark.req("RF-11")
def test_get_returns_every_field_including_the_password(auth_client):
    created = _create(auth_client).json()

    response = auth_client.get(f"{URL}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {**created, "password": FULL["password"]}


@pytest.mark.req("RF-08", "RN-06")
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("title", "t" * 101),
        ("title", ""),
        ("password", ""),
        ("password", "p" * 1025),
        ("username", "u" * 256),
        ("url", "javascript:alert(1)"),
        ("url", "ftp://x"),
        ("url", "http://"),
        ("url", "https://a.co/" + "p" * 2040),
        ("url", " https://a.co"),
        ("url", "ht\ntps://evil.example"),
        ("url", "https://a.co/\tpath"),
        ("url", "https://a.co/a b"),
        ("notes", "n" * 10_001),
    ],
)
def test_create_rejects_values_outside_rn06(auth_client, field, value):
    response = _create(auth_client, **{field: value})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert not value or value not in response.text


@pytest.mark.req("RF-08", "RN-06")
def test_create_accepts_the_upper_boundaries(auth_client):
    response = _create(
        auth_client,
        title="t" * 100,
        password="p" * 1024,
        username="u" * 255,
        url="http://a.co/" + "p" * (2048 - len("http://a.co/")),
        notes="n" * 10_000,
    )

    assert response.status_code == 201


@pytest.mark.req("RF-08")
def test_create_requires_title_and_password(auth_client):
    response = auth_client.post(URL, json={"username": "x"})

    fields = {d["field"] for d in response.json()["error"]["details"]}
    assert response.status_code == 422 and fields == {"title", "password"}


@pytest.mark.req("RF-09", "RN-08", "RN-13")
def test_list_is_sorted_by_title_paginated_and_has_no_secrets(auth_client):
    for title in ["b", "A", "c", "D"]:
        _create(auth_client, title=title)

    page = auth_client.get(URL, params={"limit": 2, "offset": 1})

    assert page.status_code == 200
    body = page.json()
    assert (body["total"], body["limit"], body["offset"]) == (4, 2, 1)
    assert _ids(page) == ["b", "c"]
    for item in body["items"]:
        assert set(item) == {"id", "title", "username", "url", "created_at", "updated_at"}
    assert FULL["password"] not in page.text and "notes" not in page.text


@pytest.mark.req("RF-09", "RN-13")
def test_list_defaults_and_offset_beyond_total(auth_client):
    _create(auth_client)

    default = auth_client.get(URL).json()
    beyond = auth_client.get(URL, params={"offset": 50})

    assert (default["limit"], default["offset"], default["total"]) == (20, 0, 1)
    assert beyond.status_code == 200
    assert beyond.json()["items"] == [] and beyond.json()["total"] == 1


@pytest.mark.req("RN-13")
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "x"}])
def test_list_rejects_invalid_pagination(auth_client, params):
    assert auth_client.get(URL, params=params).status_code == 422


@pytest.mark.req("RF-10", "RN-15", "RN-08")
def test_search_is_case_insensitive_on_title_username_and_url(auth_client):
    _create(auth_client, title="Banco do Brasil", username="x", url=None)
    _create(auth_client, title="Outro", username="JoaoSilva", url=None)
    _create(auth_client, title="Terceiro", username="y", url="https://Exemplo.com/login")

    assert _ids(auth_client.get(URL, params={"q": "BANCO"})) == ["Banco do Brasil"]
    assert _ids(auth_client.get(URL, params={"q": "joaosilva"})) == ["Outro"]
    by_url = auth_client.get(URL, params={"q": "EXEMPLO.COM"})
    assert _ids(by_url) == ["Terceiro"] and by_url.json()["total"] == 1
    none = auth_client.get(URL, params={"q": "inexistente"})
    assert none.json()["items"] == [] and none.json()["total"] == 0
    assert "password" not in auth_client.get(URL, params={"q": "o"}).text


@pytest.mark.req("RF-12", "RN-06")
def test_patch_changes_only_the_sent_fields(auth_client, clock):
    created = _create(auth_client).json()
    clock.advance(minutes=5)

    response = auth_client.patch(
        f"{URL}/{created['id']}", json={"title": "Novo", "password": "nova"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Novo" and body["username"] == "ana" and "password" not in body
    assert (
        body["created_at"] == created["created_at"] and body["updated_at"] > created["updated_at"]
    )
    assert auth_client.get(f"{URL}/{created['id']}").json()["password"] == "nova"


@pytest.mark.req("RF-12")
def test_patch_accepts_null_to_clear_optional_fields(auth_client):
    created = _create(auth_client).json()

    body = auth_client.patch(
        f"{URL}/{created['id']}", json={"username": None, "url": None, "notes": None}
    ).json()

    assert (body["username"], body["url"], body["notes"]) == (None, None, None)
    assert body["title"] == "Banco"


@pytest.mark.req("RF-12")
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": None},
        {"password": None},
        {"title": "  "},
        {"title": "t" * 101},
        {"url": "ftp://x"},
    ],
)
def test_patch_rejects_empty_or_invalid_bodies(auth_client, payload):
    created = _create(auth_client).json()

    response = auth_client.patch(f"{URL}/{created['id']}", json=payload)

    assert response.status_code == 422
    assert auth_client.get(f"{URL}/{created['id']}").json()["title"] == "Banco"


@pytest.mark.req("RF-13")
def test_delete_removes_the_credential(auth_client):
    created = _create(auth_client).json()

    assert auth_client.delete(f"{URL}/{created['id']}").status_code == 204
    assert auth_client.get(f"{URL}/{created['id']}").status_code == 404
    assert auth_client.delete(f"{URL}/{created['id']}").status_code == 404
    assert auth_client.get(URL).json()["total"] == 0


@pytest.mark.req("RN-09", "RNF-03")
def test_other_users_credentials_look_nonexistent(auth_client_factory):
    ana = auth_client_factory("ana@email.com")
    bia = auth_client_factory("bia@email.com")
    secret_id = _create(ana).json()["id"]

    for response in (
        bia.get(f"{URL}/{secret_id}"),
        bia.patch(f"{URL}/{secret_id}", json={"title": "roubado"}),
        bia.delete(f"{URL}/{secret_id}"),
    ):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
    assert bia.get(URL).json()["total"] == 0
    assert ana.get(f"{URL}/{secret_id}").json()["title"] == "Banco"


@pytest.mark.req("RNF-03")
def test_unknown_uuid_and_other_users_id_give_the_same_response(auth_client_factory):
    ana = auth_client_factory("ana@email.com")
    bia = auth_client_factory("bia@email.com")
    foreign = _create(ana).json()["id"]

    unknown = bia.get(f"{URL}/00000000-0000-4000-8000-000000000000")
    other = bia.get(f"{URL}/{foreign}")

    assert unknown.status_code == other.status_code == 404
    assert unknown.json() == other.json()


@pytest.mark.req("RF-11", "RNF-03")
@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_id_that_is_not_a_uuid_returns_422(auth_client, method):
    # PATCH gets a valid body, so the 422 can only come from the id.
    kwargs = {"json": {"title": "x"}} if method == "patch" else {}

    response = getattr(auth_client, method)(f"{URL}/nao-e-uuid", **kwargs)

    assert response.status_code == 422


@pytest.mark.req("RN-07")
def test_vault_limit_returns_409_and_frees_up_after_a_delete(small_vault):
    ids = [_create(small_vault, title=str(n)).json()["id"] for n in range(3)]

    blocked = _create(small_vault, title="quarta")

    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "VAULT_LIMIT_REACHED"
    assert small_vault.delete(f"{URL}/{ids[0]}").status_code == 204
    assert _create(small_vault, title="quarta").status_code == 201


@pytest.mark.req("RF-08", "RF-09", "RF-10", "RF-11", "RF-12", "RF-13", "RN-09")
@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("post", URL, {"json": FULL}),
        ("get", URL, {}),
        ("get", f"{URL}/00000000-0000-4000-8000-000000000000", {}),
        ("patch", f"{URL}/00000000-0000-4000-8000-000000000000", {"json": {"title": "x"}}),
        ("delete", f"{URL}/00000000-0000-4000-8000-000000000000", {}),
    ],
)
def test_every_route_requires_a_session(client, method, path, kwargs):
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.req("RF-11", "RN-05")
def test_credentials_are_readable_from_any_new_session(client, auth_client):
    created = _create(auth_client).json()
    token = login(client, auth_client.user.email, auth_client.user.password).json()["token"]

    response = client.get(f"{URL}/{created['id']}", headers=bearer(token))

    assert response.json()["password"] == FULL["password"]


@pytest.mark.req("RF-06", "RN-12")
def test_changing_the_master_password_keeps_every_credential_readable(client, auth_client):
    created = _create(auth_client).json()
    new_password = "outra-senha-mestra-456"

    changed = client.put(
        "/api/v1/accounts/me/master-password",
        json={"current_master_password": VALID_PASSWORD, "new_master_password": new_password},
        headers=bearer(auth_client.token),
    )
    token = login(client, auth_client.user.email, new_password).json()["token"]

    assert changed.status_code == 204
    assert (
        client.get(f"{URL}/{created['id']}", headers=bearer(token)).json()["password"]
        == FULL["password"]
    )


@pytest.mark.req("RF-07", "RN-12")
def test_deleting_the_account_deletes_its_credentials(app, auth_client_factory):
    from sqlalchemy import text

    ana = auth_client_factory("ana@email.com")
    bia = auth_client_factory("bia@email.com")
    _create(ana)
    _create(bia)

    deletion = ana.post("/api/v1/accounts/me/deletion", json={"master_password": VALID_PASSWORD})

    assert deletion.status_code == 204
    with app.state.engine.connect() as connection:
        rows = connection.execute(text("SELECT user_id FROM credentials")).all()
    assert [row.user_id for row in rows] == [bia.user.id]


@pytest.mark.req("RN-07", "RNF-03")
def test_parallel_creates_cannot_exceed_the_vault_limit(small_vault):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda n: _create(small_vault, title=str(n)), range(10))
        statuses = [response.status_code for response in results]

    assert statuses.count(201) == 3 and statuses.count(409) == 7
    assert small_vault.get(URL).json()["total"] == 3


@pytest.mark.req("RF-12")
def test_parallel_patches_of_different_fields_do_not_overwrite_each_other(auth_client):
    for round_number in range(8):
        created = _create(auth_client, title=f"c{round_number}").json()
        url = f"{URL}/{created['id']}"
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(auth_client.patch, url, json={"username": "novo-usuario"})
            second = pool.submit(auth_client.patch, url, json={"notes": "novas-notas"})
            assert first.result().status_code == second.result().status_code == 200

        stored = auth_client.get(url).json()
        assert (stored["username"], stored["notes"]) == ("novo-usuario", "novas-notas")
