"""Diagnostic routes registered only by the test suite (research R19)."""

from fastapi import APIRouter
from pydantic import BaseModel

from cofre.core.errors import CofreError

router = APIRouter(prefix="/api/v1/_probe")


class EchoIn(BaseModel):
    name: str


@router.post("/echo")
def echo(payload: EchoIn) -> dict[str, str]:
    return {"name": payload.name}


@router.get("/boom")
def boom() -> None:
    raise RuntimeError("MARCADOR-EXCECAO")


@router.get("/unknown-code")
def unknown_code() -> None:
    raise CofreError("NOT_IN_CATALOG", 418)
