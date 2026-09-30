"""Compose stack for smoke tests (research R21).

The ``cofre-smoke`` project name isolates containers and volume from the development stack,
so ``down -v`` never touches the local database. A missing Docker fails the tests instead of
skipping them, to avoid a false green.
"""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT = "cofre-smoke"
BASE_URL = "http://localhost:8000"


def compose(*args: str, check: bool = True, timeout: float = 600) -> subprocess.CompletedProcess:
    docker = shutil.which("docker")
    if docker is None:
        pytest.fail("Docker não encontrado no PATH: os testes de fumaça exigem Docker.")
    return subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [docker, "compose", "-p", PROJECT, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
        timeout=timeout,
    )


@pytest.fixture(scope="session")
def compose_stack() -> Iterator[str]:
    try:
        compose("up", "-d", "--build", "--wait", "api")
    except subprocess.CalledProcessError as exc:
        compose("down", "-v", check=False)
        pytest.fail(f"docker compose up falhou:\n{exc.stdout}\n{exc.stderr}")
    try:
        yield BASE_URL
    finally:
        compose("down", "-v", check=False)
