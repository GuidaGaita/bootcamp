# Implementation Plan: Cofre de credenciais

**Branch**: `spec/002-003-contas-e-cofre` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md) | **Contrato**: [contracts/api.md](contracts/api.md)

## Summary

CRUD de credenciais com todos os campos cifrados (ADR-0010), usando a sessão e a DEK da unidade 002. Sem dependências novas.

**Constitution Check**: I ✅ · II ✅ (AES-GCM com AAD por usuário e credencial; nenhum campo em log) · III ✅ testes primeiro, `req` em todos · IV ✅ contrato em `contracts/api.md`, `services` sem FastAPI · V ✅ busca em memória, sem índices nem bibliotecas novas.

## Project Structure

```text
src/cofre/
├── repositories/  models.py (+ Credential) · credentials.py (todas as consultas filtram por user_id)
├── services/      vault.py (VaultService: create, list, get, update, delete; AAD; limite; busca)
└── api/           schemas/credentials.py · routers/credentials.py · deps.py (get_vault_service)
tests/             api/test_credentials.py · security/test_vault_storage.py · perf/test_vault_perf.py
```

## Decisões de implementação

- **Conteúdo cifrado:** JSON UTF-8 `{"title","username","password","url","notes"}` (docs/04 §3.2). O `VaultService` decifra com a DEK do `AuthContext`; a DEK nunca é guardada.
- **Listagem e busca** decifram todas as credenciais do usuário (≤ 1.000), filtram, ordenam por `casefold()` do título e `id`, e paginam em memória.
- **Validação (RN-06)** nos schemas Pydantic (`Field(max_length=...)`, validador de esquema da URL); os erros saem pelo handler 422 da unidade 001.
- **`PATCH`** usa `model_fields_set` para distinguir "não enviado" de `null`; `title` e `password` não aceitam `null`.
- **Falha de decifragem** vira `DataIntegrityError` (`CofreError` com código `INTERNAL_ERROR`, status 500).
- **Teste `perf`:** semeia 1.000 credenciais de 1 KB pelo serviço, mede p95 das operações e fica fora da seleção padrão.
