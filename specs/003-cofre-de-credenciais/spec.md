# Feature Specification: Cofre de credenciais

**Feature Branch**: `spec/002-003-contas-e-cofre`

**Created**: 2026-09-30

**Status**: Implementada

**Versão**: 1.0.0

**Input**: User description: "Unidade 003 — Cofre de credenciais. Escopo: RF-08 a RF-13; RN-06 a RN-09, RN-13, RN-15; RNF-01, RNF-03, RNF-12. CRUD de credenciais cifradas por usuário, com listagem paginada e busca."

> **Fontes normativas.** [docs/02](../../docs/02-requisitos.md) (RF/RN), [docs/03](../../docs/03-arquitetura.md) (modelo, endpoints, erros), [docs/04](../../docs/04-seguranca.md) (AES-GCM, AAD) e [docs/07](../../docs/07-estrategia-de-testes.md) §4. O contrato está em [contracts/api.md](contracts/api.md). Depende da unidade 002 (sessão e DEK).

## Clarifications

### Session 2026-09-30

- RNF-04 só permite a senha na consulta individual (RF-11). Por isso **criar (RF-08) e atualizar (RF-12) respondem sem `password`**; a listagem e a busca também (RN-08).
- Um item de listagem traz `id`, `title`, `username`, `url`, `created_at` e `updated_at`; `notes` só aparece na criação, na atualização e na consulta individual.
- O limite de 1.000 credenciais (RN-07) vem de `COFRE_MAX_CREDENTIALS_PER_USER`; os testes usam um valor pequeno nessa configuração, em vez de criar 1.001 itens.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar e consultar credencial (Priority: P1)

**Independent Test**: `uv run pytest tests/api/test_credentials.py -k "create or get"`

1. **Given** sessão válida, **When** `POST /api/v1/credentials` com `title` e `password`, **Then** 201 com a credencial **sem** `password`.
2. **Given** a credencial criada, **When** `GET /api/v1/credentials/{id}`, **Then** 200 com todos os campos, inclusive a senha decifrada.
3. **Given** dados fora de RN-06, **Then** 422 `VALIDATION_ERROR`; acima do limite do cofre, 409 `VAULT_LIMIT_REACHED`.
4. **Given** nenhuma credencial em claro no SQLite, **When** se inspeciona o arquivo, **Then** título, senha, usuário, URL e notas não aparecem (RNF-01).

### User Story 2 - Listar e buscar (Priority: P1)

**Independent Test**: `uv run pytest tests/api/test_credentials.py -k "list or search"`

1. **Given** várias credenciais, **When** `GET /api/v1/credentials`, **Then** `{items, total, limit, offset}` ordenado por título, sem `password`.
2. **Given** `q`, **Then** só as que contêm o termo (sem diferenciar caixa) em título, usuário ou URL.
3. **Given** `limit` fora de 1–100 ou `offset` negativo, **Then** 422; `offset` além do total devolve lista vazia com `total` correto.

### User Story 3 - Atualizar e excluir (Priority: P1)

**Independent Test**: `uv run pytest tests/api/test_credentials.py -k "update or delete"`

1. **Given** uma credencial, **When** `PATCH` com parte dos campos, **Then** 200 com os campos alterados e os demais intactos; novo nonce a cada cifragem.
2. **Given** `PATCH` vazio ou anulando `title`/`password`, **Then** 422.
3. **When** `DELETE`, **Then** 204 e a credencial deixa de existir (404).

### User Story 4 - Isolamento entre usuários (Priority: P1)

**Independent Test**: `uv run pytest tests/api/test_credentials.py tests/security/test_vault_storage.py -k "other_user or tamper or unauth"`

1. **Given** a credencial de outro usuário, **When** `GET`, `PATCH` ou `DELETE`, **Then** 404, igual a um UUID inexistente (RNF-03).
2. **Given** um `ciphertext` adulterado ou trocado entre linhas, **When** é lido, **Then** falha a decifragem e a resposta é 500 `INTERNAL_ERROR` sem detalhes (A6).
3. **Given** ausência de token, **Then** 401 `UNAUTHENTICATED` em todas as rotas.

## Edge Cases

Todos os casos da unidade 003 em [docs/07 §4](../../docs/07-estrategia-de-testes.md) são obrigatórios: `title` só com espaços e com 100/101 caracteres; `password` com 1024/1025 e `notes` com 10.000/10.001; `url` com `javascript:` ou `ftp:`; `PATCH` vazio ou anulando campos obrigatórios; ID que não é UUID (422), inexistente e de outro usuário (404); limite do cofre; `limit` 0/101 e `offset` além do total; busca em outra caixa; nenhum item de listagem com `password`.

Transversais de docs/07: bytes do SQLite sem texto claro (RNF-01); adulteração de `ciphertext` e troca entre usuários falham (A6); nenhuma senha em logs (RNF-04).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `POST /api/v1/credentials` DEVE criar a credencial do usuário autenticado e responder 201 com `id`, `title`, `username`, `url`, `notes`, `created_at` e `updated_at`, **sem** `password` (RF-08, RNF-04).
- **FR-002**: Os campos DEVEM obedecer RN-06: `title` 1–100 caracteres não vazio após remover espaços; `password` 1–1024; `username` ≤ 255; `url` ≤ 2048 com esquema `http` ou `https`; `notes` ≤ 10.000. Títulos duplicados são permitidos (RN-06).
- **FR-003**: Todos os campos DEVEM ser armazenados num único `ciphertext` AES-256-GCM (`nonce ‖ texto cifrado ‖ tag`) com a DEK do usuário e AAD `cofre:credential:v{enc_version}:{user_id}:{credential_id}`; `enc_version` = 1; cada cifragem usa nonce novo; nada fica em claro no banco (RNF-01, docs/04 §3.2).
- **FR-004**: A criação DEVE responder 409 `VAULT_LIMIT_REACHED` quando o usuário já tem `COFRE_MAX_CREDENTIALS_PER_USER` credenciais (RN-07).
- **FR-005**: `GET /api/v1/credentials` DEVE listar, decifrando o cofre do usuário em memória, ordenado por `title` (sem diferenciar caixa) e depois por `id`, em `{items, total, limit, offset}`; `limit` 1–100 (padrão 20), `offset` ≥ 0; `offset` além do total devolve lista vazia; nenhum item contém `password` nem `notes` (RF-09, RN-08, RN-13).
- **FR-006**: O parâmetro `q` DEVE filtrar por substring, sem diferenciar caixa, em título, usuário e URL, e `total` conta os resultados da busca (RF-10, RN-15).
- **FR-007**: `GET /api/v1/credentials/{id}` DEVE responder 200 com todos os campos, inclusive `password` (RF-11).
- **FR-008**: `PATCH /api/v1/credentials/{id}` DEVE alterar só os campos enviados, recifrar com novo nonce, atualizar `updated_at` e responder 200 sem `password`; corpo vazio ou `title`/`password` nulos → 422; `username`, `url` e `notes` aceitam `null` para limpar (RF-12).
- **FR-009**: `DELETE /api/v1/credentials/{id}` DEVE remover a credencial e responder 204 (RF-13).
- **FR-010**: Toda consulta DEVE filtrar por `user_id` no repositório; `id` inexistente ou de outro usuário → 404 `NOT_FOUND`; `id` que não é UUID → 422 (RN-09, RNF-03).
- **FR-011**: Falha na decifragem (adulteração, AAD diferente) DEVE responder 500 `INTERNAL_ERROR` sem detalhes (docs/04 A6).
- **FR-012**: Todas as rotas DEVEM exigir sessão válida (401 `UNAUTHENTICATED`) e o código NÃO DEVE registrar em log nenhum campo da credencial (RNF-04).
- **FR-013**: Com um cofre de 1.000 credenciais de até 1 KB, as operações do cofre DEVEM ter p95 < 200 ms em ambiente local, verificado por teste `perf` fora da suíte padrão (RNF-12).

### Key Entities

- **Credential** (`credentials`): `id`, `user_id`, `ciphertext`, `enc_version`, `created_at`, `updated_at`, conforme docs/03 §3.

## Success Criteria *(mandatory)*

- **SC-001**: CRUD completo com dois usuários, sem vazamento entre eles.
- **SC-002**: 100% dos casos de borda acima têm teste `req`; RF-08 a RF-13 e RN-06 a RN-09, RN-13 e RN-15 aparecem em `reports/rastreabilidade.md`.
- **SC-003**: Suíte verde, cobertura ≥ 85%, `ruff` limpo e CI verde.
- **SC-004**: O teste `perf` passa a meta de RNF-12 na máquina do mantenedor.

## Assumptions

- A busca e a ordenação ocorrem em memória porque todos os campos são cifrados (ADR-0010).
- Esta spec foi escrita sem `/speckit-clarify` e `/speckit-analyze`, por economia.

## Histórico de revisões

| Versão | Data | Mudança | Motivo | Origem |
|--------|------|---------|--------|--------|
| 1.0.0 | 2026-09-30 | Versão aprovada | — | PR de spec das unidades 002 e 003 |
| 1.0.0 | 2026-10-01 | Status alterado para Implementada; conteúdo sem mudança | Fase B concluída | PR de implementação da unidade 003 |
