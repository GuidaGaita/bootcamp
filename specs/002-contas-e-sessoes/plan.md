# Implementation Plan: Contas e sessões

**Branch**: `spec/002-003-contas-e-cofre` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md) | **Contrato**: [contracts/api.md](contracts/api.md)

## Summary

Cadastro, login com bloqueio, sessões com token opaco, logout, consulta, troca de senha mestra e exclusão. As decisões criptográficas e de modelo já estão em docs/03 e docs/04 (ADR-0008, ADR-0009); este plano só as mapeia para arquivos.

## Technical Context

**Dependências novas** (runtime): `argon2-cffi`, `cryptography` (únicas permitidas, docs/04 §5). Sem `email-validator`: o formato do e-mail (RN-01) é uma expressão regular simples.
**Testes**: como na unidade 001; Argon2id reduzido por `COFRE_ENV=test`; relógio `FakeClock`.
**Constitution Check**: I ✅ spec aprovada antes do código · II ✅ regras de docs/04 §5 viram FR-013 · III ✅ `tasks.md` com testes primeiro · IV ✅ contrato em `contracts/api.md`, camadas respeitadas · V ✅ sem bibliotecas além das duas exigidas, sem Alembic.

## Project Structure

```text
src/cofre/
├── crypto/        hashing.py (NFKC, Argon2id, hash fictício) · kdf.py (KEK) · cipher.py (AES-GCM, nonce‖ct‖tag)
│                  keys.py (DEK, embrulho, chave de sessão HKDF, AADs) · tokens.py (gerar, decodificar, SHA-256)
├── repositories/  models.py (User, Session, LoginThrottle) · users.py · sessions.py · login_throttles.py
├── services/      validation.py (RN-01, RN-02) · throttle.py (RN-14/16) · accounts.py · sessions.py
└── api/           schemas/accounts.py, sessions.py · routers/accounts.py, sessions.py · deps.py (serviços, contexto)
tests/             unit/test_crypto.py, test_validation.py · api/test_accounts.py, test_sessions.py, test_account_management.py
                   security/test_auth_hygiene.py · conftest.py (fixtures FR-015)
```

## Decisões de implementação

- **Erros.** `CofreError` ganha `headers` (para `Retry-After`) e `details` (para 422 de regras de negócio); o handler os repassa. Novos códigos entram em `CATALOG` (FR-014).
- **Datas.** Coluna `UTCDateTime` (grava UTC sem fuso e devolve `datetime` com fuso), porque o SQLite descarta o fuso.
- **IDs** são `str(uuid4())`. Exclusões explícitas de sessões e credenciais (o SQLite não aplica chave estrangeira por padrão).
- **Transação.** O serviço faz `commit` antes de lançar um erro que precisa persistir efeito (contador de falhas, revogação de sessões).
- **Hash fictício.** Calculado uma vez por combinação de parâmetros (`functools.cache`), para igualar o tempo do login com e-mail inexistente.
- **Autenticação.** `get_auth_context` lê o cabeçalho, chama `SessionService.resolve` e devolve `AuthContext(user_id, session_id, dek)`.
- **Arquitetura.** O teste `test_architecture.py` passa a incluir `crypto` (não importa nenhuma outra camada).
