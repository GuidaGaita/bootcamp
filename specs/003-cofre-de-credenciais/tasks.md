---

description: "Lista de tarefas da unidade 003 — Cofre de credenciais"
---

# Tasks: Cofre de credenciais

**Input**: `specs/003-cofre-de-credenciais/` e docs/02, 03, 04, 07. Depende da unidade 002 implementada.

**Tests**: obrigatórios e escritos antes; todo teste com `@pytest.mark.req(...)`. Ciclos locais com `--no-cov`.

**Issues**: uma issue por unidade (`unidade:003`).

## Phase 1: Testes primeiro

- [X] T001 [P] Escrever `tests/api/test_credentials.py` (`req("RF-08".."RF-13","RN-06".."RN-09","RN-13","RN-15","RNF-03")`), usando `auth_client`/`auth_client_factory`: criar (201 sem `password`), consultar (com `password`), limites de RN-06 (100/101, 1024/1025, 10.000/10.001, título só com espaços, `javascript:` e `ftp:`), listar com paginação e ordenação, `limit` 0/101, `offset` além do total, busca em outra caixa (título, usuário, URL), nenhum item com `password`, `PATCH` parcial e vazio, anular `title`/`password`, `DELETE`, ID não UUID/inexistente/de outro usuário (422/404/404), limite do cofre com `max_credentials_per_user` pequeno, 401 sem token.
- [X] T002 [P] Escrever `tests/security/test_vault_storage.py` (`req("RNF-01","RNF-03","RNF-04")`): o arquivo SQLite não contém título, senha, usuário, URL nem notas em claro; `ciphertext` adulterado → 500 `INTERNAL_ERROR` sem detalhes; `ciphertext` de outro usuário copiado para a linha de outra credencial → falha (AAD); dois cifrados da mesma credencial têm nonces diferentes; a senha não aparece em logs nem nas respostas de criação, atualização e listagem.

## Phase 2: Implementação

- [X] T003 Acrescentar `Credential` a `repositories/models.py` e criar `repositories/credentials.py` (inserir, obter por `(id, user_id)`, listar e contar por `user_id`, atualizar, excluir), sempre filtrando por `user_id` (FR-010).
- [X] T004 Implementar `services/vault.py` (`VaultService`), `DataIntegrityError` em `core/errors.py` e `VAULT_LIMIT_REACHED` no catálogo, até os testes de T001/T002 referentes a regras e cifragem passarem (FR-001 a FR-011).
- [X] T005 Implementar `api/schemas/credentials.py`, `api/routers/credentials.py` e `get_vault_service` em `api/deps.py`, incluindo o roteador em `create_app`, até T001 e T002 passarem (FR-001 a FR-012).

## Phase 3: Desempenho e fechamento

- [X] T006 Escrever `tests/perf/test_vault_perf.py` (`@pytest.mark.perf`, `req("RNF-12")`) com 1.000 credenciais de 1 KB e p95 < 200 ms para criar, listar, consultar e atualizar (FR-013); rodar com `uv run pytest -m perf --no-cov`.
- [X] T007 Rodar `uv run pytest`, `ruff check` e `ruff format --check`; atualizar docs/02 §4, README, roadmap, spec (status `Implementada`) e publicar `docs/relatorios/AAAA-MM-DD-incremento-3.md`.
