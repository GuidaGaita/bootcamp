---

description: "Lista de tarefas da unidade 001 — Fundação da API"
---

# Tasks: Fundação da API

**Input**: Design documents from `/specs/001-fundacao-da-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: **obrigatórios**. A constituição (princípio III) exige TDD: em cada fase, as tarefas de teste vêm antes da implementação e precisam **falhar** antes dela. Todo teste de aceitação ou de borda recebe `@pytest.mark.req(...)` com os IDs indicados na tarefa.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Projeto único, layout `src/` (plan.md §Project Structure): código em `src/cofre/`, testes e harness em `tests/`, infraestrutura na raiz.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Criar `pyproject.toml` (nome `cofre`, versão `0.2.0`, `requires-python = ">=3.13,<3.14"`, *build backend* `uv_build`, dependências `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`; grupo `dev` com `pytest`, `pytest-cov`, `pytest-randomly`, `httpx`, `jsonschema`, `pyyaml`, `ruff`), `.python-version` com `3.13`, e gerar `uv.lock` com `uv lock` (research R1–R3; FR-034, FR-035)
- [ ] T002 Configurar `[tool.ruff]` em `pyproject.toml`: `target-version = "py313"`, `line-length = 100`, `select = ["E", "W", "F", "I", "B", "UP", "S", "ANN", "N"]`, `ignore = ["ANN202"]`, `per-file-ignores` para `tests/**` com `S101` e `ANN` (research R17; FR-038)
- [ ] T003 Configurar `[tool.pytest.ini_options]` e `[tool.coverage]` em `pyproject.toml`: `testpaths = ["tests"]`; marcadores `unit`, `integration`, `api`, `security`, `perf`, `smoke`, `req`; `addopts` com `--strict-markers -m "not perf and not smoke" --cov=cofre --cov-branch --cov-fail-under=85 --cov-report=term-missing --cov-report=xml:reports/coverage.xml --cov-report=html:reports/htmlcov --junitxml=reports/junit.xml`; `[tool.coverage.run] source = ["cofre"]`, `branch = true` (research R14; FR-023, FR-024, FR-027, FR-028)
- [ ] T004 [P] Criar o esqueleto de pacotes: `src/cofre/__init__.py` com `__version__ = "0.2.0"` e `__init__.py` vazios em `src/cofre/core/`, `src/cofre/api/`, `src/cofre/api/routers/`, `src/cofre/api/schemas/`, `src/cofre/services/`, `src/cofre/repositories/`, `tests/harness/` e `tests/support/` (plan.md)
- [ ] T005 [P] Criar `.env.example` com todas as variáveis `COFRE_*` de docs/08 §3, seus padrões e uma linha de descrição cada (FR-018)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Escrever `tests/unit/test_clock.py` (marcador `unit`, `req("RNF-09")`): `SystemClock.now()` retorna `datetime` com `tzinfo` UTC; `FakeClock` começa em `2026-01-01T00:00:00Z`, só muda com `advance(minutes=...)` e `set(...)`, e `set` rejeita `datetime` sem fuso (FR-021)
- [ ] T007 Implementar `Clock` (Protocol) e `SystemClock` em `src/cofre/core/clock.py` e `FakeClock` em `tests/support/clock.py` até T006 passar (research R9; FR-021)
- [ ] T008 [P] Escrever `tests/unit/test_architecture.py` (marcador `unit`, `req("RNF-11")`): percorre `src/cofre` com `ast` e falha se `core` importar outra camada, se `repositories` importar `services`/`api` ou se `services` importar `api`, `fastapi` ou `starlette` (research R18; constituição IV)
- [ ] T009 Implementar `Settings` em `src/cofre/core/config.py` com `pydantic-settings` (`env_prefix="COFRE_"`, `frozen=True`, `extra="ignore"`) e **todos** os campos e padrões da tabela *Settings* de data-model.md, ainda sem validadores personalizados (FR-018)
- [ ] T010 [P] Escrever `tests/integration/test_database.py` (marcador `integration`, `req("RF-01")`): `ping` funciona com arquivo SQLite em `tmp_path`; `ping` lança erro quando a URL aponta para um diretório; `init_schema` cria o diretório pai ausente; a sessão aberta por `session_factory` executa `SELECT 1` e é fechada (research R6, R7; FR-003)
- [ ] T011 Implementar `src/cofre/repositories/database.py` com `Base` (declarativa, sem tabelas), `build_engine(url)` com `connect_args={"check_same_thread": False}`, `build_session_factory(engine)`, `ping(engine)` com `SELECT 1` numa conexão nova e `init_schema(engine, url)` que cria o diretório pai do arquivo SQLite e executa `Base.metadata.create_all`, até T010 passar (research R6, R7)
- [ ] T012 Implementar `create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI` em `src/cofre/main.py` e as dependências `get_settings`, `get_clock` e `get_db` em `src/cofre/api/deps.py`: lê `Settings()` e usa `SystemClock` só quando os argumentos são `None`; guarda `settings`, `clock`, *engine* e *session factory* em `app.state`; *lifespan* executa `init_schema` registrando `database_init_failed` (só o tipo da exceção) sem derrubar a aplicação e descarta o *engine* no encerramento; `title="Cofre API"` e `version=cofre.__version__`; nenhuma leitura de ambiente na importação (FR-003, FR-017, FR-022)
- [ ] T013 Criar `tests/support/probe.py` com `APIRouter` contendo `POST /api/v1/_probe/echo` (corpo com campo obrigatório `name: str`) e `GET /api/v1/_probe/boom` (lança `RuntimeError("MARCADOR-EXCECAO")`), e `tests/conftest.py` com as fixtures `settings` (`COFRE_ENV=test`, Argon2id reduzido, banco em `tmp_path`), `clock` (`FakeClock`), `app` (`create_app(settings, clock)` com o roteador de diagnóstico incluído) e `client` (`TestClient`). Não registrar o plugin do harness aqui: ele entra em T036 (research R19; FR-029)
- [ ] T014 [P] Escrever `tests/unit/test_contract_support.py` (marcador `unit`, `req("RNF-08")`): o utilitário de contrato aceita `{"status": "ok"}` para `GET /health` 200, rejeita campo extra, rejeita `details` fora de `VALIDATION_ERROR`, rejeita `code` diferente do componente `NotFound` e falha quando falta o cabeçalho obrigatório `X-Request-ID` (research R13; FR-030)
- [ ] T015 Implementar `tests/support/contract.py` com `assert_response_matches(response, *, operation=None, component=None)`, que carrega `specs/001-fundacao-da-api/contracts/openapi.yaml` uma vez e valida corpo com `jsonschema.Draft202012Validator` (referências `#/components/...` resolvidas no próprio documento) e cabeçalhos com `required: true`, até T014 passar (research R13; ADR-0016)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Verificação de saúde da API (Priority: P1) 🎯 MVP

**Goal**: `GET /health` responde 200 `{"status": "ok"}` com o banco acessível e 503 `SERVICE_UNAVAILABLE` sem detalhes internos quando não está, refletindo a recuperação sem reinício.

**Independent Test**: `uv run pytest tests/api/test_health.py tests/integration/test_health_service.py`

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Escrever `tests/api/test_health.py` (marcador `api`, `req("RF-01")`), com todas as respostas validadas por `assert_response_matches`:
  - 200 com corpo exato `{"status": "ok"}` sem cabeçalho `Authorization`;
  - 503 `SERVICE_UNAVAILABLE` com `COFRE_DATABASE_URL` apontando para `tmp_path` (diretório), sem o caminho do banco, `sqlite`, `Traceback` nem nome de exceção no corpo;
  - aplicação iniciada com o banco indisponível sobe e responde 503;
  - recuperação sem reinício: o diretório pai do banco começa como arquivo (503), o teste o troca por diretório e a próxima chamada responde 200.

  Cobre US1 cenários 1–4 e FR-001 a FR-003.
- [ ] T017 [P] [US1] Escrever `tests/integration/test_health_service.py` (marcador `integration`, `req("RF-01")`): `HealthService.check()` retorna `HealthStatus.OK` com banco acessível e lança `ServiceUnavailableError` com banco inacessível (FR-002, FR-003)

### Implementation for User Story 1

- [ ] T018 [US1] Implementar `CofreError(code: str, status: int)` e `ServiceUnavailableError` (`code="SERVICE_UNAVAILABLE"`, `status=503`) em `src/cofre/core/errors.py`, sem dependência de outras camadas (research R5)
- [ ] T019 [US1] Implementar `HealthStatus` e `HealthService(engine)` com `check()` em `src/cofre/services/health.py`, sem importar FastAPI/Starlette, até T017 passar (FR-002, FR-003)
- [ ] T020 [US1] Implementar `ErrorResponse`, `ErrorBody` e `ValidationDetail` em `src/cofre/api/schemas/errors.py` (`details` opcional, lista não vazia de `{field, issue}`) e, em `src/cofre/api/errors.py`, o catálogo `code → (status, message)` com os textos da tabela *Códigos usados na unidade 001* de data-model.md e o handler de `CofreError` que monta o corpo padronizado sem `details` (FR-005)
- [ ] T021 [US1] Implementar `HealthResponse` em `src/cofre/api/schemas/health.py`, a dependência `get_health_service` em `src/cofre/api/deps.py` e o roteador `GET /health` em `src/cofre/api/routers/health.py` (fora de `/api/v1`, respostas 200 `HealthResponse` e 503 `ErrorResponse` declaradas no OpenAPI), incluídos em `create_app` com o handler de T020, até T016 passar (FR-001, FR-002, FR-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Contrato HTTP uniforme: erros e cabeçalhos (Priority: P1)

**Goal**: todo erro sai no formato padronizado com `code` estável e mensagem pt-BR, `/api/v1` sempre com `Cache-Control: no-store` e OpenAPI publicado.

**Independent Test**: `uv run pytest tests/api/test_errors.py tests/api/test_headers.py tests/api/test_openapi.py tests/unit/test_error_catalog.py`

### Tests for User Story 2 ⚠️

- [ ] T022 [P] [US2] Escrever `tests/api/test_errors.py` (marcador `api`, `req("RNF-08", "RNF-14")`; os casos de valor não ecoado e do 500 também com `"RNF-04"`), com todas as respostas validadas por `assert_response_matches(component=...)`:
  - `GET /api/v1/rota-inexistente` → 404 `NOT_FOUND`;
  - `POST /health` → 405 `METHOD_NOT_ALLOWED` com cabeçalho `Allow: GET`;
  - `POST /api/v1/_probe/echo` com corpo `{"name": ` → 422 com `details == [{"field": "body", "issue": "JSON malformado."}]`;
  - corpo `{}` → 422 com `details == [{"field": "name", "issue": "Campo obrigatório."}]`;
  - corpo `{"name": ["MARCADOR-VALOR"]}` → 422 sem `MARCADOR-VALOR` na resposta;
  - `GET /api/v1/_probe/boom` → 500 `INTERNAL_ERROR` sem `MARCADOR-EXCECAO`, `RuntimeError` nem `Traceback` no corpo.

  Cobre US2 cenários 1–4 e FR-005 a FR-009.
- [ ] T023 [P] [US2] Escrever `tests/api/test_headers.py` (marcador `api`, `req("RNF-04", "RNF-08")`): `Cache-Control: no-store` nas respostas 404 de `/api/v1` e `/api/v1/rota-inexistente`, 422 de `/api/v1/_probe/echo` e 500 de `/api/v1/_probe/boom`, e na resposta 405 de `DELETE /api/v1/_probe/echo`; `/api/v10/x` e `/health` **não** são obrigados a tê-lo (o teste só verifica que o prefixo não casa `/api/v10`) (FR-010)
- [ ] T024 [P] [US2] Escrever `tests/api/test_openapi.py` (marcador `api`, `req("RNF-08")`): `GET /openapi.json` retorna documento com `openapi` iniciando por `3.`, `info.title == "Cofre API"` e, para cada operação e status de `contracts/openapi.yaml`, a mesma operação e status; `GET /docs` retorna 200 HTML (US2 cenário 5; FR-004)
- [ ] T025 [P] [US2] Escrever `tests/unit/test_error_catalog.py` (marcador `unit`, `req("RNF-14", "RNF-04")`), com a função de mapeamento de erros do Pydantic:
  - todo `code` do catálogo pertence ao enum `ErrorCode` do contrato e tem mensagem não vazia;
  - `("body", 12)` com tipo `json_invalid` → `field="body"`;
  - `("body", "name")` com tipo `missing` → `field="name"` e `"Campo obrigatório."`;
  - `("query", "limit")` com tipo `int_parsing` → `field="limit"` e `"Tipo de valor inválido."`;
  - tipo desconhecido → `"Valor inválido."`;
  - o `input` do erro nunca aparece no resultado.

  Cobre FR-005 e FR-009.

### Implementation for User Story 2

- [ ] T026 [US2] Estender `src/cofre/api/errors.py`, até T022 (exceto o 500) e T025 passarem:
  - handler de `StarletteHTTPException`: 404 → `NOT_FOUND`; 405 → `METHOD_NOT_ALLOWED`, preservando os cabeçalhos da exceção (`Allow`); status fora do catálogo → 500 `INTERNAL_ERROR` com log ERROR;
  - handler de `RequestValidationError` → 422 `VALIDATION_ERROR`, com `details` gerado pela função de mapeamento: localização sem o primeiro segmento quando ele é `body`, `query`, `path`, `header` ou `cookie`; `body` para `json_invalid` ou quando não sobra segmento; tabela *Textos de issue* de data-model.md.

  Cobre research R5.
- [ ] T027 [US2] Implementar `RequestContextMiddleware` como middleware ASGI puro em `src/cofre/api/middleware.py`, registrado em `create_app` como o mais externo entre os de usuário, até T022 (500) e T023 passarem. Nesta etapa ele:
  - intercepta `http.response.start` para acrescentar `Cache-Control: no-store` quando `path == "/api/v1"` ou começa por `"/api/v1/"`;
  - captura exceções não tratadas e envia 500 `INTERNAL_ERROR` padronizado, com o mesmo acréscimo de cabeçalho, sem relançar.

  Cobre research R4 e R12, ADR-0015, FR-008 e FR-010.
- [ ] T028 [US2] Declarar a resposta 503 com `ErrorResponse` e a descrição de `/health` no roteador e ajustar os metadados do OpenAPI em `create_app` até T024 passar (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Harness de testes rastreável com gate de qualidade (Priority: P1)

**Goal**: `uv run pytest` valida o marcador `req` contra docs/02, gera `reports/rastreabilidade.md` e `reports/pytest-output.log` e aplica o gate de 85% só na seleção padrão.

**Independent Test**: `uv run pytest tests/unit/test_harness_catalog.py tests/unit/test_harness_traceability.py tests/unit/test_harness_coverage_gate.py --no-cov`

### Tests for User Story 3 ⚠️

Os testes com `pytester.runpytest_subprocess` criam, no diretório temporário, um `pyproject.toml` com a opção ini `requirements_catalog` apontando para um catálogo de exemplo e um pacote mínimo de exemplo.

- [ ] T029 [P] [US3] Escrever `tests/unit/test_harness_catalog.py` (marcador `unit`, `req("RNF-09")`): o leitor extrai de um catálogo de exemplo `RF-01` com prioridade `Must`, `RNF-12` com `Should` e `RN-01` sem prioridade, ignora linhas fora de tabela e, sobre o `docs/02-requisitos.md` real, encontra `RF-01` a `RF-16`, `RNF-01` a `RNF-15` e `RN-01` a `RN-16` (data-model.md *Catálogo de requisitos*; FR-025)
- [ ] T030 [P] [US3] Escrever `tests/unit/test_harness_traceability.py` (marcador `unit`, `req("RNF-09")`), cobrindo US3 cenários 2, 3, 5 e 6 e FR-024 a FR-026:
  - `req("RF-1")` → execução falha citando o *nodeid* e `RF-1`;
  - `req("RF-99")` → falha citando `RF-99`;
  - `req()` → falha;
  - marcador não registrado → falha (`--strict-markers`);
  - teste com `req("RF-01")` aparece sob `RF-01` em `reports/rastreabilidade.md`, com o resultado;
  - requisito `Must` sem teste aparece na seção "Requisitos Must sem teste" sem alterar o código de saída;
  - com um teste falhando, `rastreabilidade.md` é gerado mesmo assim.
- [ ] T031 [P] [US3] Escrever `tests/unit/test_harness_coverage_gate.py` (marcador `unit`, `req("RNF-09")`), cobrindo US3 cenários 1 e 4 e FR-027 e FR-028:
  - seleção padrão com cobertura abaixo de 85% → código de saída diferente de 0 mesmo com todos os testes passando;
  - a mesma suíte com `-m unit`, com `-k nome` ou com caminho de arquivo explícito → código 0;
  - com um teste falhando, `reports/junit.xml`, `reports/coverage.xml`, `reports/htmlcov/index.html` e `reports/pytest-output.log` existem, e o log contém o resumo final.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implementar `tests/harness/catalog.py`: `load_catalog(path) -> dict[str, str | None]` lendo linhas de tabela que começam por `| RF-\d{2} |`, `| RNF-\d{2} |` ou `| RN-\d{2} |` e capturando a prioridade (`Must`, `Should`, `Could`, `Won't`) quando houver, até T029 passar (research R14)
- [ ] T033 [P] [US3] Implementar `tests/harness/traceability.py`, até T030 passar. Cobre research R14:
  - opção ini `requirements_catalog`, com padrão `docs/02-requisitos.md` relativo ao *rootdir*;
  - em `pytest_collection_modifyitems`, valida cada `req` (ao menos um ID, formato `^(RF|RNF|RN)-\d{2}$`, existência no catálogo) e reúne as violações num único `pytest.UsageError`;
  - em `pytest_runtest_logreport`, registra os resultados;
  - em `pytest_sessionfinish`, escreve `reports/rastreabilidade.md` no formato de data-model.md, com instante UTC, seleção (padrão/subconjunto), tabela requisito → testes → resultado e a seção "Requisitos Must sem teste".
- [ ] T034 [P] [US3] Implementar `tests/harness/coverage_gate.py`: em `pytest_configure`, zera `config.option.cov_fail_under` quando a expressão `-m` difere de `not perf and not smoke`, quando há `-k` ou quando os argumentos não são os `testpaths`, até T031 (gate) passar (research R14)
- [ ] T035 [P] [US3] Implementar `tests/harness/output_log.py`: em `pytest_configure` (`trylast`), duplica a escrita do *terminal writer* para `reports/pytest-output.log`, como o plugin `pastebin` do pytest, e fecha o arquivo em `pytest_unconfigure`, até T031 (log) passar (research R14)
- [ ] T036 [US3] Criar `tests/harness/plugin.py`, que registra os hooks de T033–T035, e declarar em `tests/conftest.py` `pytest_plugins = ["pytester", "tests.harness.plugin"]`, ajustando `pythonpath` em `pyproject.toml` se necessário; rodar `uv run pytest` e confirmar os cinco artefatos em `reports/` (FR-026, FR-028)

**Checkpoint**: Harness completo; a partir daqui todo teste novo aparece em `reports/rastreabilidade.md`

---

## Phase 6: User Story 4 - Ambiente reprodutível e integração contínua (Priority: P2)

**Goal**: `docker compose up` e `docker compose run --rm tests` funcionam num clone limpo, e o CI roda `lint` → `test` → `docker`.

**Independent Test**: `uv run pytest -m smoke --no-cov` e `uv run pytest tests/unit/test_ci_workflow.py --no-cov`; execução real dos três jobs no PR de implementação.

### Tests for User Story 4 ⚠️

- [ ] T037 [P] [US4] Escrever os testes da US4 (research R21), cobrindo US4 cenários 1–4 e FR-036 e FR-037:
  - **`tests/smoke/conftest.py`:** *fixture* de sessão `compose_stack` com `docker compose -p cofre-smoke up -d --build --wait api` e `down -v` no encerramento; falha, sem pular, se o Docker não estiver disponível.
  - **`tests/smoke/test_compose_stack.py`** (marcador `smoke`):
    - `/health` responde 200 com `{"status": "ok"}` e `X-Request-ID` (`req("RF-01", "RNF-10")`);
    - `/docs` responde 200 (`req("RNF-08", "RNF-10")`);
    - `exec -T api id -u` retorna valor diferente de `0` (`req("RNF-10", "RNF-15")`);
    - após `restart api`, `exec -T api test -f /data/cofre.db` tem sucesso (`req("RNF-10")`);
    - `run --rm tests pytest tests/unit/test_clock.py --no-cov` grava `reports/junit.xml` no host (`req("RNF-10")`).
  - **`tests/unit/test_ci_workflow.py`** (marcador `unit`, `req("RNF-10", "RNF-11")`): lê `.github/workflows/ci.yml` e verifica:
    - gatilhos `pull_request`/`push` para `develop` e `main`;
    - jobs `lint` → `test` → `docker` via `needs`;
    - presença de `uv lock --check`, `ruff check`, `ruff format --check`, `pytest`, `pytest -m smoke` e `docker compose run --rm tests`;
    - `upload-artifact` de `reports` com `if: always()`.

### Implementation for User Story 4

- [ ] T038 [P] [US4] Criar `Dockerfile` e `.dockerignore` (research R15). O `.dockerignore` exclui `.git`, `.venv`, `reports`, `data`, `__pycache__`, `.pytest_cache`, `.ruff_cache` e `.claude`. Estágios do `Dockerfile`:
  - `base`: `python:3.13-slim` com o binário do `uv` copiado de `ghcr.io/astral-sh/uv` numa versão fixa, e `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`;
  - `build`: `uv sync --frozen --no-dev --no-install-project` só com `pyproject.toml` e `uv.lock`, depois `src/` e `uv sync --frozen --no-dev`;
  - `runtime`: usuário `cofre` UID 10001, `/data` do usuário, `EXPOSE 8000`, `HEALTHCHECK` com `python -c` e `urllib` em `/health`, `CMD ["uvicorn", "cofre.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]`;
  - `test`: `uv sync --frozen` com o grupo `dev`, cópia de `tests/`, `specs/` e `docs/02-requisitos.md`, `PATH` com `/app/.venv/bin`, `CMD ["pytest"]`.

  Cobre FR-032, FR-033 e FR-034.
- [ ] T039 [US4] Criar `docker-compose.yml` (research R15), cobrindo FR-032 e FR-033:
  - serviço `api`: `target: runtime`, `ports: ["8000:8000"]`, `COFRE_ENV=production`, `COFRE_DATABASE_URL=sqlite:////data/cofre.db`, volume `cofre-data:/data` e `healthcheck`;
  - serviço `tests`: `target: test`, `profiles: ["tests"]`, `COFRE_ENV=test`, volume `./reports:/app/reports` e `user: root`, justificado em comentário;
  - volume nomeado `cofre-data`.
- [ ] T040 [P] [US4] Criar `.github/workflows/ci.yml` (research R16; FR-034, FR-037):
  - gatilhos `pull_request` e `push` para `develop` e `main`;
  - `permissions: contents: read` e `concurrency` com `cancel-in-progress`;
  - job `lint`: `astral-sh/setup-uv` com Python 3.13, `uv lock --check`, `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`;
  - job `test` (`needs: lint`): `uv sync --locked`, `uv run pytest`, `actions/upload-artifact` de `reports/` com `if: always()`;
  - job `docker` (`needs: test`): `astral-sh/setup-uv`, `uv sync --locked`, `uv run pytest -m smoke --no-cov` e `docker compose run --rm tests`.

  O workflow deve fazer T037 (`test_ci_workflow.py`) passar.
- [ ] T041 [US4] Executar os cenários de `quickstart.md` na máquina Windows do mantenedor, anotando os resultados para o relatório de execução (FR-035; SC-001, SC-003; docs/02 RNF-15 "uso local em Windows"):
  - cenários 1 a 3, 5 e 6, com Docker;
  - cenários 7 a 10, com `uv`, sem Docker;
  - tempo de `/health` com `curl -w "%{time_total}"`, com o banco disponível e indisponível.

**Checkpoint**: ambiente reprodutível e CI prontos; os PRs seguintes já passam pelos três jobs

---

## Phase 7: User Story 5 - Configuração e inicialização seguras (Priority: P2)

**Goal**: configuração só por `COFRE_*`, valores inválidos ou inseguros impedem a inicialização sem ecoar valores, e aplicações criadas pela fábrica são independentes.

**Independent Test**: `uv run pytest tests/unit/test_config.py tests/security/test_startup_guards.py tests/api/test_app_factory.py`

### Tests for User Story 5 ⚠️

- [ ] T042 [P] [US5] Escrever `tests/unit/test_config.py` (marcador `unit`, `req("RNF-10")`; casos de mensagem também com `"RNF-04"`), com as variáveis definidas via `monkeypatch.setenv`. Cobre US5 cenário 1 e FR-018 e FR-019:
  - sem variáveis, os padrões de data-model.md;
  - `COFRE_LOG_LEVEL=debug` normalizado para `DEBUG`;
  - erro de configuração em cada caso: `COFRE_ENV=staging`; `COFRE_LOG_LEVEL=verbose`; `0` e `-1` em `COFRE_SESSION_TTL_MINUTES`, `COFRE_LOGIN_MAX_ATTEMPTS`, `COFRE_LOGIN_LOCK_MINUTES` e `COFRE_MAX_CREDENTIALS_PER_USER`; `COFRE_DATABASE_URL=postgresql://MARCADOR-URL/db`;
  - a mensagem do `ConfigurationError` cita o nome da variável e não contém `staging`, `verbose`, `MARCADOR-URL` nem o valor numérico recebido.
- [ ] T043 [P] [US5] Escrever `tests/security/test_startup_guards.py` (marcador `security`, `req("RNF-02")`), cobrindo US5 cenários 2 e 3 e FR-020:
  - com `COFRE_ENV=production` e também com `development`, `create_app()` falha para `COFRE_ARGON2_MEMORY_KIB=19455`, `COFRE_ARGON2_TIME_COST=1` e `COFRE_ARGON2_PARALLELISM=0`, cada um isoladamente;
  - com os valores mínimos exatos (19456, 2, 1), a aplicação inicia;
  - com `COFRE_ENV=test` e `COFRE_ARGON2_MEMORY_KIB=1024`, a aplicação inicia.
- [ ] T044 [P] [US5] Escrever `tests/api/test_app_factory.py` (marcador `api`, `req("RNF-09", "RNF-10")`; caso do banco padrão também com `"RNF-15"`), cobrindo US5 cenário 5 e FR-017 e FR-022:
  - `create_app()` sem argumentos usa `Settings` do ambiente e `SystemClock`;
  - `importlib.reload(cofre.main)` com `COFRE_ENV=staging` no ambiente não falha;
  - duas aplicações com `tmp_path` e `FakeClock` diferentes não compartilham banco (arquivos distintos criados) nem relógio;
  - com `monkeypatch.chdir(tmp_path)` e sem `COFRE_DATABASE_URL`, `/health` responde 200 e cria `tmp_path/data/cofre.db`.

### Implementation for User Story 5

- [ ] T045 [US5] Acrescentar a `src/cofre/core/config.py` os validadores e a exceção de configuração, até T042–T044 passarem (research R8; FR-019, FR-020):
  - `env` e `log_level` como `Literal`, com `log_level` normalizado em maiúsculas;
  - inteiros `≥ 1`;
  - `database_url` com *backend* `sqlite` via `sqlalchemy.engine.make_url`;
  - validador de modelo com os mínimos OWASP do Argon2id quando `env != "test"`;
  - `ConfigurationError`, cuja mensagem lista `COFRE_<CAMPO>` e o motivo sem o valor.

  Em `src/cofre/main.py`, converter `ValidationError` em `ConfigurationError`.

**Checkpoint**: configuração validada; parâmetros fracos não chegam à unidade 002

---

## Phase 8: User Story 6 - Identificação e registro de requisições (Priority: P3)

**Goal**: toda resposta com `X-Request-ID` validado e uma linha de log JSON por requisição, sem dados sensíveis.

**Independent Test**: `uv run pytest tests/unit/test_request_id.py tests/unit/test_json_formatter.py tests/api/test_request_logging.py tests/security/test_log_hygiene.py`

### Tests for User Story 6 ⚠️

- [ ] T046 [P] [US6] Escrever `tests/unit/test_request_id.py` (marcador `unit`, `req("RNF-13", "RNF-04")`) para a função de escolha do identificador sobre cabeçalhos brutos (FR-012):
  - são propagados: `abc-123`, um valor com 64 caracteres válidos e `A-z-0-9`;
  - geram UUID v4 novo (verificado com `uuid.UUID(valor).version == 4`): valor com 65 caracteres, valor vazio, valor com `\n`, valor com espaço, `ação`, cabeçalho ausente e dois cabeçalhos `x-request-id`.
- [ ] T047 [P] [US6] Escrever `tests/unit/test_json_formatter.py` (marcador `unit`, `req("RNF-13")`): cada registro vira uma única linha JSON válida com `timestamp`, `level` e `event`; `timestamp` vem do campo extra quando fornecido e de `record.created` em UTC quando não; a pilha de uma exceção vira lista `arquivo:linha:função` sem a mensagem `MARCADOR-EXCECAO`; `configure_logging` chamada duas vezes instala um único *handler* (FR-013, FR-015)
- [ ] T048 [P] [US6] Escrever `tests/api/test_request_logging.py` (marcador `api`, `req("RNF-13")`), com logs capturados por `caplog`. Cobre US6 cenários 1–3, US5 cenário 4 e FR-011, FR-013, FR-015 e FR-016:
  - `X-Request-ID: abc-123` → cabeçalho e `request_id` do log iguais a `abc-123`;
  - sem o cabeçalho → UUID v4 igual no cabeçalho e no log;
  - dois cabeçalhos `X-Request-ID` enviados como lista de tuplas → UUID gerado;
  - `X-Request-ID` presente em `/health`, `/docs`, `/openapi.json`, 404, 405, 422 e 500;
  - exatamente um registro `event="request"` por chamada, com `method`, `status` e `duration_ms ≥ 0`;
  - `route == "/health"` em `/health` e `route is None` em `/api/v1/rota-inexistente`;
  - `timestamp` igual ao instante do `FakeClock` após `clock.advance(minutes=5)`;
  - com `log_level="WARNING"` na configuração, nenhum registro `request`;
  - `/api/v1/_probe/boom` gera registro ERROR `unhandled_exception` com `error_type == "RuntimeError"` e `stack` não vazia, sem `MARCADOR-EXCECAO`.
- [ ] T049 [P] [US6] Escrever `tests/security/test_log_hygiene.py` (marcador `security`, `req("RNF-04", "RNF-13")`), cobrindo US6 cenário 4 e FR-014:
  - uma requisição a `POST /api/v1/_probe/echo?q=MARCADOR-QUERY` com `Authorization: Bearer MARCADOR-TOKEN`, `Cookie: s=MARCADOR-COOKIE`, corpo `{"name": "MARCADOR-CORPO"}` e `X-Request-ID: MARCADOR\nINJETADO`;
  - outra requisição sem corpo a `GET /api/v1/rota-inexistente` com os mesmos cabeçalhos;
  - em ambas, nenhum marcador aparece em `caplog.text` nem na saída capturada por `capsys`.

### Implementation for User Story 6

- [ ] T050 [US6] Implementar `src/cofre/core/logging.py` com `JsonFormatter` (uma linha JSON; campos extras permitidos `timestamp`, `event`, `request_id`, `method`, `route`, `status`, `duration_ms`, `error_type`, `stack`; nunca `record.msg` com dados de requisição) e `configure_logging()` idempotente sobre o logger `cofre` com `StreamHandler(stdout)`, até T047 passar (research R10)
- [ ] T051 [US6] Estender `RequestContextMiddleware` em `src/cofre/api/middleware.py`, até T046, T048 e T049 passarem. Cobre research R4, R10 e R11 e FR-011 a FR-016:
  - escolher o `request_id` sobre os cabeçalhos brutos do `scope` (exatamente um `x-request-id` que case `[A-Za-z0-9-]{1,64}` em ASCII, senão `uuid4`) e guardá-lo em `scope["state"]`;
  - acrescentar `X-Request-ID` a toda resposta;
  - medir `duration_ms` com `time.perf_counter`;
  - emitir o registro `request` com `timestamp` do relógio da aplicação e `route` de `scope["route"].path` ou `None`, só se o nível configurado da aplicação permitir INFO;
  - no 500, emitir `unhandled_exception` com `error_type` e `stack` de `traceback.extract_tb`, sem `str(exc)`;
  - chamar `configure_logging()` em `create_app`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 Rodar `uv lock --check`, `uv run ruff check .`, `uv run ruff format --check .` e `uv run pytest` três vezes seguidas, com as sementes do `pytest-randomly` diferentes, e confirmar (SC-004 a SC-006; FR-031, FR-038):
  - suíte verde em menos de 60 s;
  - cobertura de linhas e ramificações ≥ 85%;
  - todo cenário de aceitação e caso de borda da spec com teste correspondente;
  - `reports/rastreabilidade.md` com testes para RF-01, RNF-08, RNF-09, RNF-10, RNF-11, RNF-13, RNF-14 e RNF-15.
- [ ] T053 [P] Atualizar a documentação no PR de implementação (docs/05 §3 passo 14):
  - `docs/02-requisitos.md` §4: RF-01, RNF-08 a RNF-11 e RNF-13 a RNF-15 como `Implementado`, com links para os testes;
  - `README.md`: status do projeto e linha "Verificação de saúde da API" como `Implementado`;
  - `docs/09-roadmap.md` §3: situação do incremento 1;
  - `specs/001-fundacao-da-api/spec.md`: status `Implementada`.
- [ ] T054 Rodar `docker compose run --rm tests` e publicar `docs/relatorios/AAAA-MM-DD-incremento-1.md` no modelo de `docs/relatorios/README.md`, com os resultados de T041 e T052; atualizar a seção *Situação* de `docs/relatorios/README.md` e a seção *Evidências de execução* do `README.md` (FR-039; research R20)
- [ ] T055 Após o merge do PR de implementação, exigir os *status checks* `lint`, `test` e `docker` na proteção de `main` e `develop` via `gh api` e atualizar a *Situação atual* de `docs/06-governanca.md` §6 num PR `docs/` (plan.md *Implementation Notes*; docs/09 critério do incremento 1)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências. T002 e T003 editam `pyproject.toml` depois de T001, portanto não são paralelos a ele.
- **Foundational (Phase 2)**: depende da Phase 1 e bloqueia todas as histórias.
- **US1 (Phase 3)**: depende da Phase 2. É o MVP.
- **US2 (Phase 4)**: depende da Phase 2; usa o catálogo de erros de T020 (US1).
- **US3 (Phase 5)**: depende da Phase 2; independe de US1 e US2 (as suítes de exemplo são sintéticas).
- **US4 (Phase 6)**: depende de US1 (teste de fumaça em `/health`) e de US3 (artefatos em `reports/`).
- **US5 (Phase 7)**: depende da Phase 2; T044 usa `/health` (US1).
- **US6 (Phase 8)**: depende de T027 (US2), porque estende o mesmo middleware.
- **Polish (Phase 9)**: depende de todas as histórias; T055 só depois do merge.

### User Story Dependencies

- **US1 (P1)**: após a Phase 2, sem dependência de outras histórias.
- **US2 (P1)**: após US1 (T020) por compartilhar `src/cofre/api/errors.py`.
- **US3 (P1)**: após a Phase 2, independente.
- **US4 (P2)**: após US1 e US3.
- **US5 (P2)**: após a Phase 2; o teste T044 precisa de US1.
- **US6 (P3)**: após US2.

### Within Each User Story

- Testes escritos e **falhando** antes da implementação.
- Modelos e erros de domínio antes de *services*; *services* antes de roteadores.
- História concluída e validada antes da próxima prioridade.

### Parallel Opportunities

- Phase 1: T004 e T005.
- Phase 2: T006, T008, T010 e T014 (arquivos de teste distintos).
- US1: T016 e T017. US2: T022 a T025. US3: T029 a T031 e depois T032 a T035. US4: T037, T038 e T040. US5: T042 a T044. US6: T046 a T049.
- US3 e US5 podem andar em paralelo com US1/US2 depois da Phase 2.

---

## Parallel Example: User Story 2

```bash
# Testes da US2 juntos (arquivos distintos):
Task: "Escrever tests/api/test_errors.py"
Task: "Escrever tests/api/test_headers.py"
Task: "Escrever tests/api/test_openapi.py"
Task: "Escrever tests/unit/test_error_catalog.py"
```

## Parallel Example: User Story 3

```bash
# Depois dos testes T029–T031, módulos do harness juntos:
Task: "Implementar tests/harness/catalog.py"
Task: "Implementar tests/harness/traceability.py"
Task: "Implementar tests/harness/coverage_gate.py"
Task: "Implementar tests/harness/output_log.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Concluir a Phase 1 (Setup).
2. Concluir a Phase 2 (Foundational).
3. Concluir a Phase 3 (US1).
4. **PARAR E VALIDAR**: `uv run pytest tests/api/test_health.py --no-cov`.

### Incremental Delivery

1. Setup + Foundational → base pronta.
2. US1 → `/health` funcionando (MVP).
3. US2 → contrato de erros e cabeçalhos.
4. US3 → harness completo; o gate e a rastreabilidade passam a valer para tudo o que vier depois.
5. US4 → Docker e CI.
6. US5 → configuração segura.
7. US6 → `X-Request-ID` e logs.
8. Polish → evidências, documentação e *status checks*.

Enquanto a cobertura total não atinge 85% nas primeiras fases, use `--no-cov` para ciclos locais de TDD; a suíte padrão com gate é exigida em T052 e no CI.

---

## Coverage Map (FR → tarefas)

| FR | Tarefas | FR | Tarefas |
|----|---------|----|---------|
| FR-001 | T016, T021 | FR-021 | T006, T007 |
| FR-002 | T016, T017, T019, T021 | FR-022 | T012, T044 |
| FR-003 | T010, T011, T012, T016, T017, T019 | FR-023 | T003, T052 |
| FR-004 | T021, T024, T028 | FR-024 | T003, T030 |
| FR-005 | T020, T022, T025, T026 | FR-025 | T029, T030, T032, T033 |
| FR-006 | T022, T026 | FR-026 | T030, T033, T036 |
| FR-007 | T022, T026 | FR-027 | T003, T031, T034 |
| FR-008 | T022, T027 | FR-028 | T003, T031, T035, T036 |
| FR-009 | T022, T025, T026 | FR-029 | T013 |
| FR-010 | T023, T027 | FR-030 | T014, T015, T016, T022 |
| FR-011 | T048, T051 | FR-031 | T052 |
| FR-012 | T046, T048, T051 | FR-032 | T038, T039, T041 |
| FR-013 | T047, T048, T050, T051 | FR-033 | T038, T039, T041 |
| FR-014 | T049, T051 | FR-034 | T001, T038, T040 |
| FR-015 | T047, T048, T050, T051 | FR-035 | T041, T044 |
| FR-016 | T048, T051 | FR-036 | T037, T038, T039, T040 |
| FR-017 | T012, T044 | FR-037 | T037, T040 |
| FR-018 | T005, T009, T042 | FR-038 | T002, T052 |
| FR-019 | T042, T045 | FR-039 | T054 |
| FR-020 | T043, T045 | | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Cada tarefa vira uma issue `T0xx: <descrição>` com as labels `tipo:tarefa` e `unidade:001` (docs/05 §3 passo 10).
- Commit por tarefa ou grupo lógico, em Conventional Commits com descrição em pt-BR.
- Pare em cada *checkpoint* para validar a história de forma independente.
- Divergência encontrada durante a implementação: pare, atualize primeiro a spec (*Histórico de revisões* + `docs/registro-de-refinamentos.md`) e só então testes e código.
