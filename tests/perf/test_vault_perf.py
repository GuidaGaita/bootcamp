"""RNF-12: p95 < 200 ms with 1,000 credentials of about 1 KB. Run with `pytest -m perf --no-cov`."""

import statistics
import time

import pytest

pytestmark = [pytest.mark.perf, pytest.mark.req("RNF-12")]

URL = "/api/v1/credentials"
LIMIT_SECONDS = 0.200
SEED = 990
SAMPLES = 20


def _p95(durations: list[float]) -> float:
    return statistics.quantiles(durations, n=20)[-1]


def _timed(call) -> float:
    started = time.perf_counter()
    response = call()
    elapsed = time.perf_counter() - started
    assert response.status_code < 300, response.text
    return elapsed


@pytest.fixture
def full_vault(auth_client):
    body = {"password": "p" * 400, "notes": "n" * 600, "url": "https://example.com/x"}
    for index in range(SEED):
        response = auth_client.post(URL, json={**body, "title": f"Credencial {index:04d}"})
        assert response.status_code == 201
    return auth_client, body


def test_vault_operations_stay_under_200_ms_at_p95(full_vault):
    client, body = full_vault
    first = client.get(URL, params={"limit": 1}).json()["items"][0]["id"]
    operations = {
        "create": lambda: client.post(URL, json={**body, "title": "nova"}),
        "list": lambda: client.get(URL, params={"limit": 100}),
        "search": lambda: client.get(URL, params={"q": "0042"}),
        "get": lambda: client.get(f"{URL}/{first}"),
        "update": lambda: client.patch(f"{URL}/{first}", json={"notes": "novas notas"}),
    }

    results = {
        name: _p95([_timed(call) for _ in range(SAMPLES if name != "create" else 9)])
        for name, call in operations.items()
    }

    print("p95 (s):", {name: round(value, 4) for name, value in results.items()})
    slow = {name: round(value, 3) for name, value in results.items() if value >= LIMIT_SECONDS}
    assert not slow, f"p95 acima de 200 ms: {slow} (todos: {results})"
