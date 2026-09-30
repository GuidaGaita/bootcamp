# Relatório de execução — Incremento 1

| Campo | Valor |
|-------|-------|
| Data | 2026-09-30 |
| Commit | `abae54e` (branch `feature/001-fundacao-da-api`) |
| Ambiente | `docker compose run --rm tests` · Python 3.13.15 · pytest 9.1.1 · imagem do estágio `test` |
| Comando | `pytest` (seleção padrão: `-m "not perf and not smoke"`, gate de 85%) |
| Semente | `--randomly-seed=2771655992` |

## Resumo

| Total | Passaram | Falharam | Pulados | Duração | Cobertura (linhas + ramificações) |
|------:|---------:|---------:|--------:|--------:|----------:|
| 155 | 155 | 0 | 0 | 11,95 s | 96,18% |

Depois desta execução, a convergência acrescentou 1 teste (T056): a suíte local passou a ter **156 testes, todos aprovados**.

Os 5 testes `smoke` ficam fora da seleção padrão e rodam à parte (`uv run pytest -m smoke --no-cov`): **5 passaram** em 19,6 s.

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 96 | ✅ |
| integration | 7 | ✅ |
| api | 41 | ✅ |
| security | 11 | ✅ |
| smoke | 5 | ✅ (execução separada) |

## Rastreabilidade

Extraído de `reports/rastreabilidade.md`. Um teste pode cobrir mais de um requisito.

| Requisito | Testes | Situação |
|-----------|-------:|----------|
| RF-01 | 12 | ✅ coberto |
| RNF-02 | 9 | ✅ coberto na parte da unidade 001 (mínimos do Argon2id na inicialização) |
| RNF-04 | 48 | ✅ coberto na parte da unidade 001 (logs e respostas sem dados sensíveis) |
| RNF-08 | 26 | ✅ coberto |
| RNF-09 | 27 | ✅ coberto |
| RNF-10 | 35 | ✅ coberto |
| RNF-11 | 15 | ✅ coberto |
| RNF-13 | 37 | ✅ coberto |
| RNF-14 | 15 | ✅ coberto |
| RNF-15 | 1 (+ execução manual no Windows abaixo) | ✅ coberto |

Requisitos *Must* sem teste: só os das unidades 002 a 005 (RF-02 a RF-04, RF-08, RF-09, RF-11 a RF-14, RNF-01 a RNF-03, RNF-05, RNF-06), ainda não implementadas.

Estabilidade: três execuções locais seguidas com sementes diferentes (`1520672812`, `369405574`, `772732954`) passaram, cada uma em cerca de 11 s (SC-004 a SC-006).

## Log (trecho)

```text
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0
Using --randomly-seed=2771655992
rootdir: /app
configfile: pyproject.toml
...
Name                                 Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------------
src/cofre/api/deps.py                   17      6      0      0    65%   14, 18, 22-26
src/cofre/api/errors.py                 53      2     10      2    94%   58->60, 81-85
src/cofre/api/middleware.py             56      0     14      1    99%   75->78
src/cofre/core/config.py                65      0     14      0   100%
src/cofre/core/errors.py                12      2      4      2    75%   12, 14
src/cofre/core/logging.py               33      0     10      0   100%
src/cofre/main.py                       37      0      4      0   100%
src/cofre/repositories/database.py      16      0      2      0   100%
src/cofre/services/health.py            15      0      0      0   100%
--------------------------------------------------------------------------------
TOTAL                                  335     10     58      5    96%
Required test coverage of 85% reached. Total coverage: 96.18%
================ 155 passed, 5 deselected, 1 warning in 11.95s =================
```

## Roteiro do quickstart (T041)

Executado em 2026-09-30 na máquina do mantenedor: Windows 11, Docker Desktop 29.7.2 e Compose v5.4.0, Python 3.13.5 e uv 0.12.13.

| Cenário | Resultado |
|---------|-----------|
| 1. API com Docker | ✅ `/health` 200 `{"status":"ok"}` com `x-request-id` UUID; `/docs` 200; `/openapi.json` descreve `/health`; `id -u` = `10001`. |
| 2. Persistência do volume | ✅ `cofre.db` continua em `/data` depois de `down` + `up`. |
| 3. Contrato de erros e cabeçalhos | ✅ 404 `NOT_FOUND` com `cache-control: no-store`; 405 `METHOD_NOT_ALLOWED` com `allow: GET`; `meu-id-123` ecoado; valor com espaço trocado por UUID. |
| 4. Logs sem dados sensíveis | ✅ uma linha JSON `event=request` por chamada, `route: null` e `status: 404` na rota inexistente; `MARCADOR` aparece 0 vez nos logs. |
| 5. Suíte em container | ✅ 155 testes, 96,18%, cinco artefatos em `reports/`. |
| 6. Teste de fumaça | ✅ 5 testes; nenhum container `cofre-smoke` restante. |
| 7. Sem Docker (Windows) | ✅ `pytest -m unit` passa sem gate (96 testes, "Seleção: subconjunto"); servidor com `uvicorn --factory` cria `./data/cofre.db` e `/health` responde 200. |
| 8. Banco indisponível | ✅ a aplicação sobe, registra `database_init_failed` só com `error_type`, e `/health` responde 503 sem caminho nem texto de exceção. |
| 9. Configuração insegura | ✅ `COFRE_ARGON2_MEMORY_KIB=1024` em produção e `COFRE_ENV=staging` encerram o processo com `ConfigurationError` que cita a variável e não cita o valor. |
| 10. Qualidade | ✅ `uv lock --check`, `ruff check` e `ruff format --check` sem erros. Os jobs do CI são verificados no PR. |

Tempo de `/health` (SC-003, meta < 1 s): 3,6 ms no container e 15,6 ms localmente com o banco disponível; 1,7 ms com o banco indisponível.

## Observações

**Refinamentos originados desta fase** ([registro](../registro-de-refinamentos.md)):

- **R-023:** o `X-Request-ID`, exigido pelo contrato nas respostas validadas pelos testes da US1 e da US2, só seria implementado na US6. A escolha do identificador foi antecipada para T021.
- **R-024:** o estágio `test` da imagem passou a copiar `.github/workflows/`, lido por `test_ci_workflow.py`.

**Erros encontrados e corrigidos durante o TDD:**

| # | Erro | Como apareceu | Correção |
|---|------|---------------|----------|
| 1 | Gate de cobertura continuava ativo em `-m unit`, `-k` e caminho explícito | Testes de autoverificação do harness (`pytester`) falharam | O `pytest-cov` guarda um *namespace* de opções próprio, criado antes da leitura completa da linha de comando. O plugin passou a zerar também `_cov.options.cov_fail_under`. |
| 2 | `UnicodeDecodeError` ao ler a saída do subprocesso no Windows | Testes do harness com mensagens em pt-BR ("inválidos") | O subprocesso escrevia em cp1252. Os testes passaram a definir `PYTHONUTF8=1` e `PYTHONIOENCODING=utf-8`. |
| 3 | `reports/pytest-output.log` com códigos de cor ANSI | Leitura do log gerado | A cópia remove as sequências de escape. Teste novo com `--color=yes`. |
| 4 | Código morto no plugin de rastreabilidade: *hook* que lia `report.config`, atributo inexistente | Revisão do código gerado pela IA antes do commit | *Hook* removido; o registro de resultados ficou numa classe ligada ao `config`. |
| 5 | Caractere de controle ESC literal gravado no código-fonte no lugar de `\x1b` | Revisão do diff | Uma edição automatizada via *shell* interpretou o escape. Arquivo corrigido e verificado com `grep`. |
| 6 | Fixture `settings` herdava variáveis `COFRE_*` do shell do desenvolvedor (ex.: `COFRE_LOG_LEVEL=WARNING` quebrava os testes de log) | `/speckit-converge` (FR-029), confirmado por teste vermelho | O `pydantic-settings` lê o ambiente mesmo com argumentos explícitos e em `model_validate`; a primeira correção proposta (`model_validate`) também falhou no teste. A solução foi a subclasse de teste `IsolatedSettings`, com `settings_customise_sources` restrito aos argumentos (T056). |

**Cobertura abaixo de 100%:**

- `api/deps.py` (65%): `get_settings`, `get_clock` e `get_db` ainda não são usados por nenhuma rota; entram na unidade 002.
- `api/errors.py`, linhas 81–85: `HTTPException` com status fora do catálogo, caminho defensivo sem rota que o provoque nesta unidade.

**Aviso conhecido:** `StarletteDeprecationWarning` recomenda `httpx2` para o `TestClient`. O projeto mantém `httpx`, conforme research R2, até a troca ser necessária.
