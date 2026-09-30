# Contrato: Contas e sessões

Formato de erro, cabeçalhos e catálogo em [docs/03 §6](../../../docs/03-arquitetura.md). Campos em `snake_case`; datas ISO 8601 em UTC. Toda resposta de `/api/v1` leva `Cache-Control: no-store` e `X-Request-ID`.

| Rota | Autenticação | Corpo da requisição | Sucesso | Erros |
|------|:------------:|---------------------|---------|-------|
| `POST /api/v1/accounts` | — | `{email: str, master_password: str}` | 201 `{id, email, created_at}` | 409 `EMAIL_ALREADY_REGISTERED`, 422 |
| `POST /api/v1/sessions` | — | `{email: str, master_password: str}` (1–1024 caracteres) | 201 `{token, expires_at}` | 401 `INVALID_CREDENTIALS`, 429 `TOO_MANY_ATTEMPTS` + `Retry-After`, 422 |
| `DELETE /api/v1/sessions/current` | Bearer | — | 204 | 401 `UNAUTHENTICATED` |
| `GET /api/v1/accounts/me` | Bearer | — | 200 `{id, email, created_at}` | 401 |
| `PUT /api/v1/accounts/me/master-password` | Bearer | `{current_master_password, new_master_password}` | 204 | 401, 403 `INVALID_MASTER_PASSWORD`, 422, 429 |
| `POST /api/v1/accounts/me/deletion` | Bearer | `{master_password}` | 204 | 401, 403 `INVALID_MASTER_PASSWORD`, 429 |

## Erros novos no catálogo

| HTTP | `code` | Mensagem (pt-BR) |
|------|--------|------------------|
| 401 | `UNAUTHENTICATED` | Autenticação necessária ou sessão inválida. |
| 401 | `INVALID_CREDENTIALS` | E-mail ou senha incorretos. |
| 403 | `INVALID_MASTER_PASSWORD` | Senha mestra incorreta. |
| 409 | `EMAIL_ALREADY_REGISTERED` | Já existe uma conta com este e-mail. |
| 429 | `TOO_MANY_ATTEMPTS` | Muitas tentativas. Tente novamente mais tarde. |

`Retry-After` é um inteiro de segundos, arredondado para cima, ≥ 1. O `details` de 422 vindo das regras RN-01/RN-02 usa `field` = `email` ou `master_password` (ou `new_master_password`) e `issue` em pt-BR sem o valor recebido.
