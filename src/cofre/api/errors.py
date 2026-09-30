"""Error catalog and exception handlers (research R5, FR-005)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cofre.api.schemas.errors import ErrorBody, ErrorResponse, ValidationDetail
from cofre.core.errors import CofreError

CATALOG: dict[str, tuple[int, str]] = {
    "NOT_FOUND": (404, "Recurso não encontrado."),
    "METHOD_NOT_ALLOWED": (405, "Método não permitido para este recurso."),
    "VALIDATION_ERROR": (422, "Os dados enviados são inválidos."),
    "INTERNAL_ERROR": (500, "Erro interno inesperado."),
    "SERVICE_UNAVAILABLE": (503, "Serviço temporariamente indisponível."),
}


def error_payload(code: str, details: list[ValidationDetail] | None = None) -> dict:
    """Body of the standard error response for a catalog ``code``."""
    _, message = CATALOG[code]
    body = ErrorBody(code=code, message=message, details=details)
    return ErrorResponse(error=body).model_dump(exclude_none=True)


def error_response(
    code: str,
    details: list[ValidationDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    status, _ = CATALOG[code]
    return JSONResponse(error_payload(code, details), status_code=status, headers=headers)


async def _handle_cofre_error(_request: Request, exc: Exception) -> JSONResponse:
    code = exc.code if isinstance(exc, CofreError) and exc.code in CATALOG else "INTERNAL_ERROR"
    return error_response(code)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CofreError, _handle_cofre_error)
