"""Account endpoints (RF-02, RF-05, RF-06, RF-07)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from cofre.api.deps import CurrentUser, get_account_service
from cofre.api.schemas.accounts import (
    AccountResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    RegisterRequest,
)
from cofre.repositories.models import User
from cofre.services.accounts import AccountService

router = APIRouter(prefix="/api/v1", tags=["accounts"])
Service = Annotated[AccountService, Depends(get_account_service)]


def _response(user: User) -> AccountResponse:
    return AccountResponse(id=user.id, email=user.email, created_at=user.created_at)


@router.post("/accounts", status_code=201, summary="Cadastra uma conta.")
def register(payload: RegisterRequest, service: Service) -> AccountResponse:
    return _response(service.register(payload.email, payload.master_password.get_secret_value()))


@router.get("/accounts/me", summary="Consulta a própria conta.")
def get_me(context: CurrentUser, service: Service) -> AccountResponse:
    return _response(service.me(context))


@router.put("/accounts/me/master-password", status_code=204, summary="Altera a senha mestra.")
def change_master_password(
    payload: ChangePasswordRequest, context: CurrentUser, service: Service
) -> None:
    service.change_master_password(
        context,
        payload.current_master_password.get_secret_value(),
        payload.new_master_password.get_secret_value(),
    )


@router.post("/accounts/me/deletion", status_code=204, summary="Exclui a própria conta.")
def delete_account(payload: DeleteAccountRequest, context: CurrentUser, service: Service) -> None:
    service.delete(context, payload.master_password.get_secret_value())
