"""Error catalog and exception handlers (research R5, FR-005)."""

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from cofre.api.schemas.errors import ErrorBody, ErrorResponse, ValidationDetail
from cofre.core.errors import CofreError

logger = logging.getLogger("cofre")

CATALOG: dict[str, tuple[int, str]] = {
    "NOT_FOUND": (404, "Recurso não encontrado."),
    "METHOD_NOT_ALLOWED": (405, "Método não permitido para este recurso."),
    "VALIDATION_ERROR": (422, "Os dados enviados são inválidos."),
    "INTERNAL_ERROR": (500, "Erro interno inesperado."),
    "SERVICE_UNAVAILABLE": (503, "Serviço temporariamente indisponível."),
}

_HTTP_STATUS_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
_LOCATION_ROOTS = {"body", "query", "path", "header", "cookie"}
_EXACT_ISSUES = {"json_invalid": "JSON malformado.", "missing": "Campo obrigatório."}
_TYPE_ISSUE = "Tipo de valor inválido."
_GENERIC_ISSUE = "Valor inválido."


def error_payload(code: str, details: list[ValidationDetail] | None = None) -> dict[str, Any]:
    """Body of the standard error response for a catalog ``code``."""
    _, message = CATALOG[code]
    body = ErrorBody(code=code, message=message, details=details)
    return ErrorResponse(error=body).model_dump(exclude_none=True)


def error_response(
    code: str,
    details: list[ValidationDetail] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    status, _ = CATALOG[code]
    return JSONResponse(error_payload(code, details), status_code=status, headers=headers)


def _issue(error_type: str) -> str:
    if error_type in _EXACT_ISSUES:
        return _EXACT_ISSUES[error_type]
    if error_type.endswith(("_type", "_parsing")):
        return _TYPE_ISSUE
    return _GENERIC_ISSUE


def _field(loc: Sequence[Any], error_type: str) -> str:
    segments = list(loc)
    if segments and segments[0] in _LOCATION_ROOTS:
        segments = segments[1:]
    if error_type == "json_invalid" or not segments:
        return "body"
    return ".".join(str(segment) for segment in segments)


def validation_details(errors: Sequence[Mapping[str, Any]]) -> list[ValidationDetail]:
    """Translate Pydantic errors without ever copying the received ``input`` (FR-009)."""
    return [
        ValidationDetail(field=_field(error["loc"], error["type"]), issue=_issue(error["type"]))
        for error in errors
    ]


async def _handle_cofre_error(_request: Request, exc: CofreError) -> JSONResponse:
    code = exc.code if exc.code in CATALOG else "INTERNAL_ERROR"
    return error_response(code)


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_STATUS_CODES.get(exc.status_code)
    if code is None:
        logger.error(
            "unmapped_http_status",
            extra={"event": "unmapped_http_status", "status": exc.status_code},
        )
        return error_response("INTERNAL_ERROR")
    return error_response(code, headers=exc.headers)


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response("VALIDATION_ERROR", details=validation_details(exc.errors()))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CofreError, _handle_cofre_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
