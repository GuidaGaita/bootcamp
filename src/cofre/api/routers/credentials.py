"""Credential endpoints (RF-08 to RF-13). The password only appears in the single GET."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from cofre.api.deps import CurrentUser, get_vault_service
from cofre.api.schemas.credentials import (
    CredentialCreate,
    CredentialFullResponse,
    CredentialItem,
    CredentialPage,
    CredentialResponse,
    CredentialUpdate,
)
from cofre.services.vault import CredentialData, VaultService

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])
Service = Annotated[VaultService, Depends(get_vault_service)]


def _public(data: CredentialData) -> CredentialResponse:
    return CredentialResponse(**{k: v for k, v in vars(data).items() if k != "password"})


@router.post("", status_code=201, summary="Cria uma credencial.")
def create(payload: CredentialCreate, context: CurrentUser, service: Service) -> CredentialResponse:
    return _public(service.create(context, payload.content()))


@router.get("", summary="Lista ou busca credenciais, sem as senhas.")
def list_credentials(
    context: CurrentUser,
    service: Service,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CredentialPage:
    items, total = service.list(context, q, limit, offset)
    return CredentialPage(
        items=[
            CredentialItem(**{k: getattr(i, k) for k in CredentialItem.model_fields}) for i in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{credential_id}", summary="Consulta uma credencial, com a senha.")
def get_credential(
    credential_id: UUID, context: CurrentUser, service: Service
) -> CredentialFullResponse:
    return CredentialFullResponse(**vars(service.get(context, str(credential_id))))


@router.patch("/{credential_id}", summary="Atualiza parcialmente uma credencial.")
def update(
    credential_id: UUID, payload: CredentialUpdate, context: CurrentUser, service: Service
) -> CredentialResponse:
    return _public(service.update(context, str(credential_id), payload.changes()))


@router.delete("/{credential_id}", status_code=204, summary="Exclui uma credencial.")
def delete(credential_id: UUID, context: CurrentUser, service: Service) -> None:
    service.delete(context, str(credential_id))
