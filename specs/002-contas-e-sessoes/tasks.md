---

description: "Lista de tarefas da unidade 002 — Contas e sessões"
---

# Tasks: Contas e sessões

**Input**: `specs/002-contas-e-sessoes/` (spec.md, plan.md, contracts/api.md) e docs/02, 03, 04, 07.

**Tests**: obrigatórios. Em cada fase, as tarefas de teste vêm antes e **falham** antes da implementação. Todo teste recebe `@pytest.mark.req(...)`. Ciclos locais com `--no-cov`; a suíte completa com gate roda no fim.

**Issues**: uma issue por unidade (`unidade:002`), sem uma issue por tarefa, por economia.

## Phase 1: Setup

- [ ] T001 `uv add argon2-cffi cryptography` (atualiza `pyproject.toml` e `uv.lock`) e estender `tests/unit/test_architecture.py` com a regra "`crypto` não importa nenhuma outra camada de `cofre`" (RNF-11).

## Phase 2: Fundação de criptografia e erros

- [ ] T002 [P] Escrever `tests/unit/test_crypto.py` (`req("RNF-01","RNF-02","RNF-05","RNF-06")`): NFKC; Argon2id verifica certo e errado; KEK determinística por salt e diferente entre sais; AES-GCM ida e volta, nonce novo a cada chamada, AAD errada, adulteração e blob com menos de 28 bytes falham; embrulho e desembrulho da DEK; chave de sessão HKDF determinística; token tem 32 bytes em base64url de 43 caracteres; `decode_token` rejeita tamanho, alfabeto e padding inválidos.
- [ ] T003 Implementar `src/cofre/crypto/` (`hashing`, `kdf`, `cipher`, `keys`, `tokens`) até T002 passar (docs/04 §3; FR-003, FR-004, FR-013).
- [ ] T004 Estender `CofreError` com `headers` e `details`, acrescentar os códigos de FR-014 ao catálogo e fazer o handler repassá-los (spec FR-014; contrato).

## Phase 3: US1 — Cadastro (P1) 🎯

- [ ] T005 [P] [US1] Escrever `tests/unit/test_validation.py` (`req("RN-01","RN-02")`) com os casos de docs/07: e-mail 254/255/sem `@`, senha 11/12/128/129, senha com o e-mail em outra caixa, acentos e emoji.
- [ ] T006 [P] [US1] Escrever em `tests/api/test_accounts.py` os testes de cadastro (`req("RF-02","RN-01","RN-02","RNF-02","RNF-04")`): 201 com e-mail normalizado; 409 para `Ana@Email.com ` e depois `ana@email.com`; 422 com `details` sem repetir o valor; o banco não contém a senha nem o `ciphertext` legível.
- [ ] T007 [US1] Implementar `repositories/models.py` (`User`, `Session`, `LoginThrottle`, `UTCDateTime`), `repositories/users.py`, `services/validation.py`, `services/accounts.py` (`register`), `api/schemas/accounts.py` e `api/routers/accounts.py` (`POST`), incluindo o roteador em `create_app`, até T005 e T006 passarem (FR-001 a FR-003).

## Phase 4: US2 — Login, sessão e logout (P1)

- [ ] T008 [P] [US2] Escrever `tests/api/test_sessions.py` (`req("RF-03","RF-04","RN-04","RN-05","RN-14","RNF-06","RNF-07")`): login 201 e `expires_at`; 401 idêntico para senha errada e e-mail inexistente; 5 falhas e 429 com `Retry-After`, inclusive com e-mail inexistente; liberação após 15 min; falhas intercaladas com sucesso; NFKC pré-composto vs. combinante; token ausente, malformado, de tamanho errado, expirado (31 min), após logout.
- [ ] T009 [US2] Implementar `repositories/login_throttles.py`, `repositories/sessions.py`, `services/throttle.py`, `services/sessions.py` (`login`, `resolve`, `logout`), `api/schemas/sessions.py`, `api/routers/sessions.py` e, em `api/deps.py`, `get_auth_context`, até T008 passar (FR-004 a FR-008).

## Phase 5: US3 — Gestão da conta (P2)

- [ ] T010 [P] [US3] Escrever `tests/api/test_account_management.py` (`req("RF-05","RF-06","RF-07","RN-05","RN-12","RN-16")`): `/me`; troca de senha (204, sessões revogadas, login antigo 401/novo 201, DEK preservada, nova senha validada por RN-02); senha atual errada 403 com a sessão válida; 5ª falha revoga as sessões e o login recebe 429; e-mail já bloqueado → 429 sem verificar a senha; exclusão remove tudo; e-mail liberado para novo cadastro.
- [ ] T011 [US3] Implementar `AccountService.me/change_master_password/delete`, os endpoints correspondentes e as regras de RN-16 até T010 passar (FR-009 a FR-012).

## Phase 6: Segurança, fixtures e fechamento

- [ ] T012 [P] Escrever `tests/security/test_auth_hygiene.py` (`req("RNF-04","RNF-05")`): senha e token não aparecem em logs, respostas de erro nem `repr` dos schemas; nenhuma chamada a `random` em `src/cofre`.
- [ ] T013 Acrescentar a `tests/conftest.py` as fixtures `make_user`, `auth_client` e `auth_client_factory` (FR-015) e usá-las nos testes das fases 4 e 5.
- [ ] T014 Rodar `uv run pytest`, `ruff check` e `ruff format --check`; atualizar docs/02 §4, README, roadmap, spec (status `Implementada`) e publicar `docs/relatorios/AAAA-MM-DD-incremento-2.md`.
