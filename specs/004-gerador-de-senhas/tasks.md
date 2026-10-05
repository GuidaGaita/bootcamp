---

description: "Lista de tarefas da unidade 004 — Gerador e avaliador de senhas"
---

# Tasks: Gerador e avaliador de senhas

**Input**: `specs/004-gerador-de-senhas/` e docs/02, 03, 04, 07. Sem dependência de outras unidades.

**Tests**: obrigatórios e escritos antes; todo teste com `@pytest.mark.req(...)`. Ciclos locais com `--no-cov`.

**Issues**: uma issue por unidade (`unidade:004`).

## Phase 1: Testes primeiro

- [X] T001 [P] Escrever `tests/unit/test_password_generator.py` (`req("RF-14","RN-10","RNF-05")`): comprimentos 8 e 128; um caractere de cada conjunto com os 4 conjuntos em comprimento 8; só os conjuntos selecionados; `exclude_ambiguous` sem `0 O o 1 l I |`; 1.000 gerações cumprindo RN-10 (com e sem `exclude_ambiguous`); fonte injetada determinística gera a mesma senha; duas gerações com a fonte real diferem; nenhum conjunto → erro.
- [X] T002 [P] Escrever `tests/unit/test_strength_estimator.py` (`req("RF-15","RN-11")`): entropia, pontuação em cada limite (28, 36, 60, 80 bits), senha comum, sequência, repetições, `weak` para pontuação ≤ 2, tempo de quebra e texto em cada faixa, limite de `1e300`, cada sugestão e a lista vazia.
- [X] T003 [P] Escrever `tests/api/test_password_generator.py` e `tests/api/test_password_strength.py` (`req("RF-14","RF-15","RN-10","RN-11")`): chamadas sem autenticação; padrões (20 caracteres); comprimento 7/8/128/129; nenhum conjunto → 422; senha a avaliar com 0/1/1024/1025 caracteres; resposta com os campos do contrato; `Cache-Control: no-store`.
- [X] T004 [P] Escrever `tests/security/test_password_hygiene.py` (`req("RNF-04","RNF-05")`): a senha avaliada não aparece na resposta, nos logs nem no `repr` do esquema; a senha gerada não aparece nos logs.

## Phase 2: Implementação

- [X] T005 Implementar `services/passwords.py` (`PasswordGenerator`, `StrengthEstimator`) até T001 e T002 passarem (FR-001 a FR-005, FR-007 a FR-010).
- [X] T006 Implementar `api/schemas/passwords.py` e `api/routers/passwords.py`, incluindo o roteador em `create_app`, até T003 e T004 passarem (FR-001, FR-002, FR-006, FR-011).

## Phase 3: Fechamento

- [X] T007 Rodar `uv run pytest`, `ruff check` e `ruff format --check`; atualizar docs/02 §4, README, roadmap, spec (status `Implementada`) e publicar `docs/relatorios/AAAA-MM-DD-incremento-4.md`.
