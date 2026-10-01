"""Session endpoints (RF-03, RF-04)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from cofre.api.deps import CurrentUser, get_session_service
from cofre.api.schemas.sessions import LoginRequest, SessionResponse
from cofre.services.sessions import SessionService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
Service = Annotated[SessionService, Depends(get_session_service)]


@router.post("", status_code=201, summary="Autentica e abre uma sessão.")
def login(payload: LoginRequest, service: Service) -> SessionResponse:
    token, expires_at = service.login(payload.email, payload.master_password.get_secret_value())
    return SessionResponse(token=token, expires_at=expires_at)


@router.delete("/current", status_code=204, summary="Encerra a sessão atual.")
def logout(context: CurrentUser, service: Service) -> None:
    service.logout(context)
