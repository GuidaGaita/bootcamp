"""``GET /health`` (RF-01)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from cofre.api.deps import get_health_service
from cofre.api.schemas.errors import ErrorResponse
from cofre.api.schemas.health import HealthResponse
from cofre.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica se a aplicação e o banco estão operacionais.",
    responses={503: {"model": ErrorResponse, "description": "Banco de dados indisponível."}},
)
def get_health(service: Annotated[HealthService, Depends(get_health_service)]) -> HealthResponse:
    return HealthResponse(status=service.check())
