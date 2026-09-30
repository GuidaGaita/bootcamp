import pytest

pytestmark = [pytest.mark.api, pytest.mark.req("RNF-04", "RNF-08")]


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "status"),
    [
        ("GET", "/api/v1", {}, 404),
        ("GET", "/api/v1/rota-inexistente", {}, 404),
        ("POST", "/api/v1/_probe/echo", {"json": {}}, 422),
        ("GET", "/api/v1/_probe/boom", {}, 500),
        ("DELETE", "/api/v1/_probe/echo", {}, 405),
    ],
)
def test_api_v1_responses_have_no_store(client, method, path, kwargs, status):
    response = client.request(method, path, **kwargs)

    assert response.status_code == status
    assert response.headers["Cache-Control"] == "no-store"


def test_prefix_does_not_match_similar_paths(client):
    response = client.get("/api/v10/x")

    assert response.status_code == 404
    assert response.headers.get("Cache-Control") != "no-store"
