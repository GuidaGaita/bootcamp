# Implementation Plan: Fundação da API

**Branch**: `spec/001-fundacao-da-api` | **Date**: 2026-09-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fundacao-da-api/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A unidade 001 entrega o esqueleto executável do Cofre: pacote `cofre` em camadas, fábrica `create_app(settings=None, clock=None)`, configuração `COFRE_*` validada, persistência SQLite pronta para as próximas unidades, `GET /health` com 200/503, contrato HTTP uniforme (erros padronizados, `Cache-Control: no-store` em `/api/v1`, `X-Request-ID` validado, log JSON por requisição) e o harness de testes com marcador `req`, relatório de rastreabilidade, gate de cobertura de linhas e ramificações e artefatos em `reports/`. Fecham a unidade a imagem Docker multi-stage, o `docker-compose.yml` com os serviços `api` e `tests` e o workflow de CI (`lint` → `test` → `docker`).

A abordagem técnica central é uma **borda HTTP concentrada num único middleware ASGI** ([ADR-0015](../../docs/adr/0015-borda-http-com-middleware-asgi-unico.md)), responsável pelo identificador da requisição, pelos cabeçalhos transversais, pelo log e pela conversão de exceções não tratadas em 500 padronizado. Os testes de API validam as respostas contra `contracts/openapi.yaml` ([ADR-0016](../../docs/adr/0016-testes-de-contrato-contra-openapi-da-spec.md)). Decisões detalhadas em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.13,<3.14"`, `.python-version` = `3.13`)

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic v2 + `pydantic-settings`, SQLAlchemy 2. Desenvolvimento: `pytest`, `pytest-cov`, `pytest-randomly`, `httpx`, `jsonschema`, `pyyaml`, `ruff` ([research.md R1–R2](research.md#r1-dependências-de-execução)).

**Storage**: SQLite via SQLAlchemy 2; sem tabelas de domínio nesta unidade ([data-model.md](data-model.md)).

**Testing**: pytest com marcadores de nível e `req`, `pytest-cov` (linhas e ramificações), `TestClient` do FastAPI, validação de contrato com `jsonschema`, `pytester` para autoverificação do harness.

**Target Platform**: Linux em container (`python:3.13-slim`); Windows e macOS via `uv` (RNF-15).

**Project Type**: web-service (API REST, projeto único com layout `src/`).

**Performance Goals**: `/health` < 1 s localmente (SC-003); suíte padrão < 60 s (SC-006).

**Constraints**: nenhum segredo, corpo, *query string* ou cabeçalho em logs (docs/04 §5); testes sem rede externa, sem `sleep` e independentes de ordem; nada lido do ambiente na importação.

**Scale/Scope**: um processo, um banco; 39 FRs, 6 histórias; base para as unidades 002 a 005.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / gate | Como o plano cumpre | Pré-pesquisa | Pós-design |
|------------------|---------------------|:------------:|:----------:|
| **I. Especificação como fonte da verdade** | Plano derivado da spec 001 (39 FRs, todos com IDs de docs/02). A lacuna do 405 foi resolvida **antes** em docs/03 (R-022). Nenhum código nesta fase. | ✅ | ✅ |
| **II. Segurança por padrão** | Logs sem corpo, *query string*, cabeçalhos ou mensagem de exceção (FR-014, FR-015); erro 500 genérico (FR-008); valores recebidos não ecoados (FR-009, FR-019); `Cache-Control: no-store` (FR-010); Argon2id abaixo do mínimo impede a inicialização fora de `test` (FR-020); `ruff` com `S311` (FR-038). Nenhuma primitiva criptográfica nesta unidade. | ✅ | ✅ |
| **III. Testes primeiro e rastreáveis** | `tasks.md` coloca os testes de cada história antes da implementação; `req` validado contra docs/02; relógio injetável; `pytest-randomly` prova a independência de ordem; gate de 85% de linhas e ramificações. | ✅ | ✅ |
| **IV. Unidades isoladas e contratos explícitos** | Contrato em [contracts/openapi.yaml](contracts/openapi.yaml) definido antes da implementação, com o formato de erro de docs/03 §6.3. Camadas `api → services → repositories → core`; `services/health.py` não importa FastAPI; um teste de arquitetura verifica as importações. | ✅ | ✅ |
| **V. Simplicidade** | Um processo e um banco; sem biblioteca de log estruturado (logging da biblioteca padrão); dependências novas justificadas em research.md; rotas de diagnóstico só na suíte de testes. | ✅ | ✅ |
| Restrições técnicas | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 + SQLite, `uv`, `pytest`, `ruff`, Docker; API em `/api/v1` com OpenAPI publicado; identificadores em inglês. | ✅ | ✅ |
| Gates de merge (Fase B) | `ruff check`/`ruff format --check` e `pytest` com cobertura ≥ 85% no job `lint`/`test`; `/speckit-analyze` sem críticos neste PR de spec. | ✅ | ✅ |
| ADRs | Duas decisões arquiteturais novas registradas: ADR-0015 (borda HTTP) e ADR-0016 (testes de contrato), com linha no README. | ✅ | ✅ |

**Resultado:** aprovado nas duas verificações, sem violações a justificar.

## Project Structure

### Documentation (this feature)

```text
specs/001-fundacao-da-api/
├── spec.md              # /speckit-specify + /speckit-clarify
├── plan.md              # Este arquivo (/speckit-plan)
├── research.md          # Fase 0 (/speckit-plan)
├── data-model.md        # Fase 1 (/speckit-plan)
├── quickstart.md        # Fase 1 (/speckit-plan)
├── contracts/
│   └── openapi.yaml     # Fase 1 (/speckit-plan)
├── checklists/
│   └── requirements.md  # Checklist de qualidade da spec
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
pyproject.toml                  # metadados, dependências, ruff, pytest, coverage
uv.lock
.python-version                 # 3.13
.env.example                    # variáveis COFRE_* documentadas
Dockerfile                      # estágios base → build → runtime / test
.dockerignore
docker-compose.yml              # serviços api e tests (perfil "tests")
.github/workflows/ci.yml        # lint → test → docker

src/cofre/
├── __init__.py                 # __version__
├── main.py                     # create_app(settings=None, clock=None)
├── core/
│   ├── __init__.py
│   ├── config.py               # Settings (pydantic-settings, COFRE_*), ConfigurationError
│   ├── clock.py                # Clock (Protocol), SystemClock
│   ├── errors.py               # CofreError e erros de domínio (ServiceUnavailableError)
│   └── logging.py              # JsonFormatter, configure_logging, stack sem mensagem
├── api/
│   ├── __init__.py
│   ├── middleware.py           # RequestContextMiddleware (ASGI puro, ADR-0015)
│   ├── errors.py               # catálogo code/status/message, handlers 404/405/422/domínio
│   ├── deps.py                 # get_settings, get_clock, get_db, get_health_service
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py           # GET /health
│   └── schemas/
│       ├── __init__.py
│       ├── errors.py           # ErrorResponse, ErrorBody, ValidationDetail
│       └── health.py           # HealthResponse
├── services/
│   ├── __init__.py
│   └── health.py               # HealthService (sem FastAPI)
└── repositories/
    ├── __init__.py
    └── database.py             # Base, build_engine, session factory, ping, init_schema

tests/
├── conftest.py                 # fixtures settings, clock, app, client; pytest_plugins
├── harness/                    # plugin do harness (não é coberto pelo gate)
│   ├── __init__.py
│   ├── plugin.py               # registra os hooks abaixo
│   ├── catalog.py              # leitura de docs/02-requisitos.md
│   ├── traceability.py         # marcador req: validação e reports/rastreabilidade.md
│   ├── coverage_gate.py        # gate só na seleção padrão completa
│   └── output_log.py           # reports/pytest-output.log (tee do terminal)
├── support/
│   ├── __init__.py
│   ├── clock.py                # FakeClock
│   ├── contract.py             # validação de respostas contra contracts/openapi.yaml
│   └── probe.py                # rotas de diagnóstico registradas só na suíte
├── unit/
│   ├── test_architecture.py    # regra de dependência entre camadas
│   ├── test_clock.py
│   ├── test_config.py
│   ├── test_error_catalog.py
│   ├── test_json_formatter.py
│   ├── test_request_id.py
│   └── test_harness_*.py       # autoverificação do harness com pytester
├── integration/
│   ├── test_database.py
│   └── test_health_service.py
├── api/
│   ├── test_health.py
│   ├── test_errors.py
│   ├── test_headers.py
│   ├── test_openapi.py
│   ├── test_request_logging.py
│   └── test_app_factory.py
├── security/
│   ├── test_log_hygiene.py
│   └── test_startup_guards.py
└── smoke/
    └── test_container_health.py
```

**Structure Decision**: projeto único com layout `src/`, seguindo docs/03 §2.3. Nesta unidade existem só as camadas usadas pela fundação: não há `crypto/` (unidade 002) nem `tests/perf/` (primeiro teste `perf` na unidade 003). O plugin do harness e os utilitários de teste ficam em `tests/`, fora do pacote `cofre`: não entram na imagem de produção nem no cálculo do gate de cobertura, e a correção deles é garantida pelos testes de autoverificação `tests/unit/test_harness_*.py`.

## Implementation Notes

- **Ordem de middlewares.** `RequestContextMiddleware` é o middleware de usuário mais externo e trata exceções não capturadas ele mesmo. Assim, o 500 sai com `X-Request-ID` e `Cache-Control`, sem depender do `ServerErrorMiddleware` do Starlette, que fica por fora dos middlewares de usuário ([research.md R4](research.md#r4-borda-http-num-único-middleware-asgi)).
- **Banco indisponível nos testes.** O 503 é provocado apontando `COFRE_DATABASE_URL` para um caminho que não pode ser aberto (um diretório, ou um arquivo no lugar do diretório pai), o que funciona igual em Windows e Linux sem *mocks* ([research.md R6](research.md#r6-verificação-do-banco-e-inicialização-tolerante)).
- **Gate de cobertura.** O `addopts` aplica `--cov-fail-under=85`, e o plugin do harness o zera quando a seleção não é a padrão (`-m`, `-k` ou caminhos explícitos) ([research.md R14](research.md#r14-harness-rastreabilidade-gate-e-log)).
- **Pós-merge da Fase B.** Os jobs `lint`, `test` e `docker` passam a ser *status checks* obrigatórios em `main` e `develop`, com atualização de docs/06 §6.
- **Fora desta unidade.** Job manual `perf` no CI (entra com o primeiro teste `perf`), fixtures de domínio (`make_user`, `auth_client`, `auth_client_factory`, `make_credential`, `raw_database`) e Alembic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação. As peças que parecem extras têm justificativa em research.md: `pytest-randomly` (independência de ordem, princípio III), `jsonschema` e `pyyaml` (testes de contrato, princípio IV) e o plugin do harness (RNF-09).
