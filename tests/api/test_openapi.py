import pytest

from tests.support.contract import load_contract

pytestmark = [pytest.mark.api, pytest.mark.req("RNF-08")]

METHODS = {"get", "post", "put", "patch", "delete"}


def _contract_operations() -> list[tuple[str, str, str]]:
    return [
        (path, method, status)
        for path, item in load_contract()["paths"].items()
        for method, operation in item.items()
        if method in METHODS
        for status in operation["responses"]
    ]


def test_openapi_document_is_published(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.")
    assert document["info"]["title"] == "Cofre API"


@pytest.mark.parametrize(("path", "method", "status"), _contract_operations())
def test_openapi_declares_contract_operations(client, path, method, status):
    document = client.get("/openapi.json").json()

    assert status in document["paths"][path][method]["responses"]


def test_interactive_docs_are_served(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
