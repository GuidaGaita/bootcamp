"""Helpers to register and log in through the public API."""

from dataclasses import dataclass

from fastapi.testclient import TestClient

VALID_PASSWORD = "senha-mestra-longa-123"


@dataclass
class User:
    email: str
    password: str
    id: str


def register(client: TestClient, email: str, password: str = VALID_PASSWORD):
    return client.post("/api/v1/accounts", json={"email": email, "master_password": password})


def login(client: TestClient, email: str, password: str = VALID_PASSWORD):
    return client.post("/api/v1/sessions", json={"email": email, "master_password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
