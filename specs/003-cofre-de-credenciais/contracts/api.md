# Contrato: Cofre de credenciais

Erros, cabeçalhos e convenções em [docs/03 §6](../../../docs/03-arquitetura.md). Todas as rotas exigem `Authorization: Bearer <token>` (401 `UNAUTHENTICATED`).

**Credential** (resposta sem senha): `{id, title, username|null, url|null, notes|null, created_at, updated_at}`.
**CredentialFull** (só na consulta individual): **Credential** + `password`.
**CredentialItem** (listagem): `{id, title, username|null, url|null, created_at, updated_at}`.

| Rota | Corpo / parâmetros | Sucesso | Erros |
|------|--------------------|---------|-------|
| `POST /api/v1/credentials` | `{title, password, username?, url?, notes?}` | 201 **Credential** | 409 `VAULT_LIMIT_REACHED`, 422 |
| `GET /api/v1/credentials` | `?q=&limit=20&offset=0` | 200 `{items: [CredentialItem], total, limit, offset}` | 422 |
| `GET /api/v1/credentials/{id}` | `id` UUID | 200 **CredentialFull** | 404, 422 |
| `PATCH /api/v1/credentials/{id}` | qualquer subconjunto de `{title, password, username, url, notes}`, ao menos um | 200 **Credential** | 404, 422 |
| `DELETE /api/v1/credentials/{id}` | — | 204 | 404, 422 |

## Erros novos no catálogo

| HTTP | `code` | Mensagem (pt-BR) |
|------|--------|------------------|
| 409 | `VAULT_LIMIT_REACHED` | Limite de credenciais atingido. |

404 `NOT_FOUND` já existe (mensagem "Recurso não encontrado."); vale também para credencial de outro usuário.
