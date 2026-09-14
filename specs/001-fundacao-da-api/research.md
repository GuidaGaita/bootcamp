# Research: Fundação da API

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Data**: 2026-09-13

Consolida as decisões técnicas da unidade 001. Cada item segue o formato *Decisão / Justificativa / Alternativas*. Não há `NEEDS CLARIFICATION` pendente no Technical Context.

## R1. Dependências de execução

- **Decisão:** `fastapi`, `uvicorn`, `pydantic-settings` e `sqlalchemy` (2.x), com limite inferior no `pyproject.toml` e versões exatas no `uv.lock`. `pydantic` v2 vem como dependência do FastAPI. `uvicorn` **sem** o extra `[standard]`.
- **Justificativa:** é o mínimo para docs/03 (FastAPI, Pydantic v2, SQLAlchemy 2, configuração por `pydantic-settings`). O extra `[standard]` traz `uvloop`, `httptools` e `watchfiles`, desnecessários para um processo único com carga baixa; `--reload` local funciona sem `watchfiles`, com *polling* (princípio V).
- **Alternativas:** `uvicorn[standard]` (mais dependências e compilação nativa sem ganho mensurável aqui); `python-dotenv` (dispensável: `pydantic-settings` já lê o ambiente e o `.env.example` é só documentação).

## R2. Dependências de desenvolvimento

- **Decisão:** grupo `dev` em `[dependency-groups]` com `pytest`, `pytest-cov`, `pytest-randomly`, `httpx`, `jsonschema`, `pyyaml` e `ruff`.
- **Justificativa:**
  - `pytest` e `pytest-cov`: ADR-0013;
  - `httpx`: exigido pelo `TestClient` do FastAPI e usado no teste de fumaça;
  - `jsonschema` e `pyyaml`: validar respostas contra `contracts/openapi.yaml` (ADR-0016);
  - `pytest-randomly`: embaralha a ordem dos testes a cada execução e imprime a semente, o que evidencia a independência de ordem exigida pelo princípio III e por SC-006.
- **Alternativas:** `schemathesis` ou `openapi-core` (mais pesados, geram testes próprios e acoplam a suíte a outra ferramenta); `pytest-xdist` (a suíte é curta; o paralelismo complicaria o log e o relatório); `mypy` (fora do escopo de RNF-11, que exige *type hints*, não checagem estática).

## R3. Empacotamento e versão do Python

- **Decisão:** layout `src/cofre`, *build backend* `uv_build`, `requires-python = ">=3.13,<3.14"`, `.python-version` com `3.13`, versão do pacote `0.2.0` exposta em `cofre.__version__` e em `info.version` do OpenAPI.
- **Justificativa:** o layout `src/` evita importar o pacote sem instalá-lo e segue docs/03 §2.3; `uv_build` dispensa uma ferramenta a mais; o limite superior garante o mesmo Python em todos os ambientes (RNF-15).
- **Alternativas:** `hatchling` (funciona, mas é uma dependência de build a mais); layout plano (mascara erros de empacotamento).

## R4. Borda HTTP num único middleware ASGI

- **Decisão:** `RequestContextMiddleware`, middleware ASGI puro e mais externo entre os de usuário, que em cada requisição:
  1. escolhe o `request_id` (R11) e o guarda em `scope["state"]`;
  2. mede a duração com `time.perf_counter`;
  3. acrescenta `X-Request-ID` a toda resposta e `Cache-Control: no-store` aos caminhos de `/api/v1` (R12);
  4. captura qualquer exceção não tratada, envia 500 `INTERNAL_ERROR` no formato padronizado e registra o log de erro (R10);
  5. emite a linha de log da requisição ao final.

  Registrado no [ADR-0015](../../docs/adr/0015-borda-http-com-middleware-asgi-unico.md).
- **Justificativa:** no Starlette, o handler de `Exception` é executado pelo `ServerErrorMiddleware`, que fica **fora** dos middlewares de usuário. Um 500 tratado ali sai sem os cabeçalhos transversais, e o `TestClient` relança a exceção por padrão. O `BaseHTTPMiddleware` tem problemas conhecidos com *streaming* e *background tasks*. Concentrar a borda num lugar só garante que nenhuma resposta, inclusive de erro, escape sem cabeçalhos e sem log.
- **Alternativas:** `@app.middleware("http")` / `BaseHTTPMiddleware` (limitações acima); handler de `Exception` (500 sem cabeçalhos); vários middlewares pequenos (ordem frágil entre eles e mais pontos de falha).

## R5. Catálogo e tradução de erros

- **Decisão:**
  - `core/errors.py` define `CofreError(code, status)` e as subclasses de domínio; nesta unidade, `ServiceUnavailableError`.
  - `api/errors.py` mantém o catálogo `code → (status, message pt-BR)` de docs/03 §6.3 e registra os handlers:
    - `StarletteHTTPException` 404 → `NOT_FOUND` e 405 → `METHOD_NOT_ALLOWED`, preservando o cabeçalho `Allow`;
    - `RequestValidationError` → 422 `VALIDATION_ERROR` com `details`;
    - `CofreError` → status e `code` do catálogo.
  - Um `HTTPException` com status fora do catálogo é tratado como 500 `INTERNAL_ERROR`, com log ERROR. Ampliar o catálogo exige atualizar docs/03 antes.
  - `details` de validação:
    - `field` é a localização do Pydantic sem o primeiro segmento quando ele é `body`, `query`, `path`, `header` ou `cookie`, com os segmentos restantes unidos por `.`;
    - para `json_invalid`, ou quando não sobra segmento, `field` é `body`;
    - `issue` vem de uma tabela por tipo de erro do Pydantic (`missing` → "Campo obrigatório.", `json_invalid` → "JSON malformado.", tipos `*_type` e `*_parsing` → "Tipo de valor inválido.", demais → "Valor inválido.").
  - O campo `input` do Pydantic **nunca** é copiado (FR-009).
- **Justificativa:** mantém o catálogo fechado e em um só lugar, com mensagens pt-BR estáveis (RNF-14), e impede que valores enviados voltem na resposta. As unidades seguintes só acrescentam códigos e entradas na tabela de `issue`.
- **Alternativas:** mensagens do Pydantic em inglês (violam RNF-14 e ecoam entrada); mapear qualquer status HTTP para um código genérico (esconde lacunas do catálogo).

## R6. Verificação do banco e inicialização tolerante

- **Decisão:**
  - `repositories/database.py` cria o `Engine` com `connect_args={"check_same_thread": False}` e expõe `ping(engine)`, que executa `SELECT 1` numa conexão nova a cada chamada.
  - No *lifespan*, a aplicação:
    1. tenta criar o diretório pai do arquivo SQLite, se ele não existir;
    2. executa `Base.metadata.create_all`, ainda sem tabelas;
    3. se o banco falhar, registra log ERROR `database_init_failed` (só o tipo da exceção) e **continua**.
  - `HealthService.check()` chama `ping` e devolve `HealthStatus.OK` ou lança `ServiceUnavailableError`.
  - O *engine* é descartado no encerramento.
- **Justificativa:** FR-003 exige que a aplicação suba com o banco indisponível e que `/health` reflita a recuperação sem reinício. Com `SELECT 1` por chamada, não há estado em cache. A criação do diretório pai faz o padrão `sqlite:///./data/cofre.db` funcionar num clone limpo.
- **Como testar sem *mocks*:**
  - indisponível: `COFRE_DATABASE_URL` aponta para `tmp_path` (um diretório), e a abertura falha em Windows e Linux;
  - recuperação: o diretório pai do banco começa como **arquivo**; o teste o remove, cria o diretório e chama `/health` de novo.
- **Alternativas:** recusar iniciar (contradiz FR-003); *health* com cache de estado (atrasa a detecção); *mock* do *engine* (não prova o comportamento com SQLite real).

## R7. Sessão de banco por requisição

- **Decisão:** `sessionmaker` guardado em `app.state` e dependência `get_db` que abre uma `Session` por requisição e a fecha ao final. Confirmar ou desfazer a transação é papel dos *services* (docs/03 §5).
- **Justificativa:** é a peça de persistência que as unidades 002 e 003 consomem; entregá-la agora, com teste de integração, evita que a unidade 002 misture fundação com regra de negócio.
- **Alternativas:** sessão global (quebra FR-022 e o isolamento de testes); adiar para a 002 (a fundação ficaria incompleta em relação ao roadmap).

## R8. Configuração

- **Decisão:**
  - `Settings(BaseSettings)` com `env_prefix="COFRE_"`, `frozen=True`, `extra="ignore"` e todos os campos de docs/08 §3 ([data-model.md](data-model.md#settings)).
  - Validadores: `env` e `log_level` como `Literal` (nível sem diferenciar caixa); inteiros `≥ 1`; `database_url` com *backend* `sqlite` (por `sqlalchemy.engine.make_url`); validador de modelo que exige os mínimos OWASP do Argon2id quando `env != "test"`.
  - `create_app` constrói `Settings()` só quando não recebe `settings`, e converte `ValidationError` em `ConfigurationError`, cuja mensagem lista apenas os nomes das variáveis (`COFRE_…`) e o motivo, sem o valor.
- **Justificativa:** docs/04 §5 regra 6 exige recusar parâmetros fracos; a mensagem padrão do Pydantic inclui `input_value`, o que violaria FR-019. Todos os campos de docs/08 entram agora porque docs/08 §3 é o contrato de configuração do projeto e a validação central evita reespecificá-lo em cada unidade; o custo é trivial.
- **Alternativas:** ler `os.environ` manualmente (sem tipos nem validação); incluir só os campos usados em 001 (as unidades 002 e 003 teriam de reabrir a validação e o `.env.example`).

## R9. Relógio

- **Decisão:** `core/clock.py` define `Clock` (`typing.Protocol` com `now() -> datetime`, sempre com fuso UTC) e `SystemClock`. O `FakeClock` fica em `tests/support/clock.py`: começa num instante fixo e só muda com `advance(**kwargs)`, que recebe os argumentos de `timedelta`, e `set(instant)`, que rejeita datas sem fuso.
- **Justificativa:** o relógio de teste não deve ir para a imagem de produção nem contar na cobertura; `Protocol` evita herança obrigatória. Nesta unidade, o relógio fornece o `timestamp` do log (FR-013); nas unidades 002 em diante, a expiração e o bloqueio.
- **Alternativas:** `freezegun` (altera o relógio global e mascara usos diretos de `datetime.now`); `FakeClock` dentro de `cofre` (código de teste em produção).

## R10. Logs estruturados

- **Decisão:**
  - Módulo `logging` da biblioteca padrão, com logger `cofre` e um `StreamHandler(stdout)` com `JsonFormatter` instalado de forma idempotente, uma única vez por processo.
  - O middleware decide pelo nível configurado **da aplicação** se emite o log, o que mantém duas aplicações independentes (FR-022) mesmo com o logger compartilhado.
  - Campos do log de requisição: `timestamp` (relógio da aplicação), `level`, `event` = `request`, `request_id`, `method`, `route`, `status`, `duration_ms`.
  - Log de erro: `event` = `unhandled_exception`, `request_id`, `error_type` e `stack` (lista de `arquivo:linha:função` de `traceback.extract_tb`), **sem** `str(exc)`.
  - `route` vem de `scope["route"].path` quando existe e é `null` caso contrário.
  - O servidor roda com `--no-access-log`.
- **Justificativa:** RNF-13 pede JSON por requisição, e RNF-04 proíbe dados sensíveis. O log de acesso do Uvicorn registra o caminho com *query string* e não é JSON. A mensagem da exceção pode carregar dados de entrada, então só a pilha é registrada. Uma biblioteca de log estruturado não é necessária para uma única linha por requisição (princípio V).
- **Alternativas:** `structlog` ou `python-json-logger` (dependência a mais); manter o log do Uvicorn (vaza a *query string*); registrar `repr(exc)` (risco de segredo em log).

## R11. `X-Request-ID`

- **Decisão:** ler os cabeçalhos brutos do `scope`. Havendo **exatamente um** `x-request-id` e o valor, decodificado em latin-1, casar `re.fullmatch(r"[A-Za-z0-9-]{1,64}", valor, re.ASCII)`, ele é usado. Nos demais casos (ausente, vazio, duplicado, longo demais, com controle ou não ASCII), usa-se `str(uuid.uuid4())`.
- **Justificativa:** docs/03 §6.2 e a clarificação da spec. Contar os cabeçalhos brutos evita que o *framework* escolha silenciosamente um de dois valores.
- **Alternativas:** aceitar e sanitizar o valor recebido (mais código e ainda ecoa conteúdo do cliente); UUID sempre (perde a correlação com sistemas externos, pedida por RNF-13).

## R12. `Cache-Control: no-store`

- **Decisão:** o middleware acrescenta o cabeçalho quando `scope["path"] == "/api/v1"` ou começa por `"/api/v1/"`, em qualquer status.
- **Justificativa:** FR-010 e a ameaça A9; a comparação com a barra evita casar prefixos como `/api/v10`.
- **Alternativas:** dependência em cada roteador (esquece rotas inexistentes e erros); aplicar a todo caminho (desnecessário para `/docs` e `/health`, fora do que a spec pede).

## R13. Testes de contrato

- **Decisão:** `tests/support/contract.py` carrega `specs/001-fundacao-da-api/contracts/openapi.yaml` uma vez e oferece:
  - `assert_response_matches(response, operation=("get", "/health"))` para operações declaradas;
  - `assert_response_matches(response, component="NotFound")` para as respostas transversais de `/api/v1`.

  A validação usa `jsonschema.Draft202012Validator`, com as referências `#/components/...` resolvidas contra o próprio documento, e confere os cabeçalhos obrigatórios declarados. `tests/api/test_openapi.py` verifica que `/openapi.json` da aplicação declara as operações e os status do contrato. Registrado no [ADR-0016](../../docs/adr/0016-testes-de-contrato-contra-openapi-da-spec.md).
- **Justificativa:** RNF-08 prevê "testes de contrato" e o princípio IV exige contrato antes da implementação; validar contra o arquivo da spec liga o teste ao artefato aprovado, e não ao que a aplicação gera.
- **Alternativas:** comparar `/openapi.json` inteiro com o arquivo (frágil: o FastAPI gera detalhes que não são contrato); `schemathesis` (R2).

## R14. Harness: rastreabilidade, gate e log

- **Decisão:**
  - **Configuração em `pyproject.toml`:** `testpaths = ["tests"]` e `addopts` com:
    - `--strict-markers` e `-m "not perf and not smoke"`;
    - `--cov=cofre --cov-branch --cov-fail-under=85`;
    - `--cov-report=term-missing`, `--cov-report=xml:reports/coverage.xml` e `--cov-report=html:reports/htmlcov`;
    - `--junitxml=reports/junit.xml`.
  - **Marcadores registrados:** `unit`, `integration`, `api`, `security`, `perf`, `smoke` e `req`.
  - **`catalog.py`:** lê `docs/02-requisitos.md` por expressão regular sobre as linhas de tabela `| RF-xx |`, `| RNF-xx |` e `| RN-xx |`, capturando ID e prioridade (RN não têm prioridade).
  - **`traceability.py`:**
    - em `pytest_collection_modifyitems`, valida cada `req` (ao menos um ID, formato e existência) e reúne as violações num único `pytest.UsageError`;
    - em `pytest_runtest_logreport`, registra o resultado de cada teste;
    - em `pytest_sessionfinish`, escreve `reports/rastreabilidade.md`, mesmo com falhas.
  - **`coverage_gate.py`:** em `pytest_configure`, zera `config.option.cov_fail_under` quando a expressão `-m` difere da padrão, quando há `-k` ou quando os argumentos não são os `testpaths`.
  - **`output_log.py`:** duplica a escrita do *terminal writer* para `reports/pytest-output.log`, como faz o plugin `pastebin` do próprio pytest.
  - **Autoverificação:** `tests/unit/test_harness_*.py` com `pytester.runpytest_subprocess` cobre marcador inválido, ID inexistente, `req` sem argumento, relatório gerado com falhas e gate só na seleção padrão.
- **Justificativa:** RNF-09, ADR-0013 e as histórias 3 e 5 da spec. Ler docs/02 mantém uma única fonte para os IDs. Os comandos de subconjunto de docs/07 §5 (`uv run pytest -m unit`) continuam funcionando sem falhar por cobertura parcial.
- **Alternativas:** lista fixa de IDs no código de teste (duplica docs/02); gate só no CI (quebra "uv run pytest com gate" de docs/07); `tee` no shell (não funciona igual no PowerShell).

## R15. Imagem Docker e compose

- **Decisão:**
  - **Dockerfile multi-stage:**
    - `base`: `python:3.13-slim` com o binário do `uv` copiado de `ghcr.io/astral-sh/uv` numa versão fixa, e `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`;
    - `build`: `uv sync --frozen --no-dev --no-install-project` com só `pyproject.toml` e `uv.lock` (camada cacheável), depois copia `src/` e roda `uv sync --frozen --no-dev`;
    - `runtime`: copia `.venv` e `src/`; usuário `cofre` (UID 10001); `/data` pertencente a ele; `EXPOSE 8000`; `HEALTHCHECK` com `python -c` e `urllib` em `/health`; `CMD uvicorn cofre.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log`;
    - `test`: a partir de `build`, `uv sync --frozen` com o grupo `dev`; copia `tests/`, `specs/` e `docs/02-requisitos.md`; `PATH` inclui `/app/.venv/bin`; `CMD ["pytest"]`.
  - **`docker-compose.yml`:**
    - serviço `api` (alvo `runtime`): porta `8000:8000`, `COFRE_ENV=production`, `COFRE_DATABASE_URL=sqlite:////data/cofre.db`, volume `cofre-data:/data` e `healthcheck`;
    - serviço `tests` (alvo `test`): `profiles: ["tests"]`, `COFRE_ENV=test`, volume `./reports:/app/reports`, `user: root`.
  - **`.dockerignore`:** exclui `.git`, `.venv`, `reports`, `data`, caches e `.claude`.
- **Justificativa:**
  - ADR-0014, com as sutilezas abaixo;
  - `--frozen` instala exatamente o lock, sem resolver dependências de novo, como define o ADR-0014; a detecção de lock desatualizado (FR-034) fica no job `lint` do CI, com `uv lock --check`, e `uv sync --locked` nos jobs do CI;
  - o perfil `tests` impede que `docker compose up` suba também a suíte, e `docker compose run --rm tests` continua funcionando porque o serviço é citado explicitamente;
  - `user: root` só no estágio de testes evita falha de permissão ao escrever no *bind mount* `./reports` em hosts Linux com UID diferente; esse estágio nunca é implantado;
  - chamar `pytest` direto pelo `PATH` evita que `uv run` tente sincronizar no container.
- **Alternativas:** imagem única com dependências de desenvolvimento (maior e com ferramentas de teste em produção); `curl` no *healthcheck* (não existe na imagem *slim*); UID do host por variável (atrito no Windows).

## R16. Integração contínua

- **Decisão:**
  - **Arquivo e disparo:** `.github/workflows/ci.yml` em `pull_request` e `push` para `develop` e `main`, com `permissions: contents: read` e `concurrency` por *ref* com cancelamento.
  - **Jobs:**
    1. `lint`: `astral-sh/setup-uv` com Python 3.13, `uv lock --check`, `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`;
    2. `test` (depois de `lint`): `uv sync --locked`, `uv run pytest`, `actions/upload-artifact` de `reports/` com `if: always()`;
    3. `docker` (depois de `test`): `uv sync --locked`, `uv run pytest -m smoke --no-cov` (os testes sobem e removem a stack `cofre-smoke`, R21) e `docker compose run --rm tests`.
  - **Ações:** fixadas na última *tag* major disponível no momento da implementação.
  - **Proteção de branches:** depois do merge do PR que cria o workflow, os três jobs viram *status checks* obrigatórios em `main` e `develop` (docs/06 §6).
- **Justificativa:** docs/07 §7 e FR-037; rodar `docker compose run --rm tests` no CI prova RNF-10 no mesmo caminho que o avaliador usa. A estrutura do próprio workflow é verificada por `tests/unit/test_ci_workflow.py` (R21), para que o cenário 4 da US4 seja um teste automatizado, como exige o princípio III.
- **Alternativas:** matriz com Windows no CI (dobra o tempo; RNF-15 aceita verificação local); job `perf` já nesta unidade (não há teste `perf`, e `pytest` sem testes coletados termina com código 5).

## R17. Lint e formatação

- **Decisão:** `ruff` com `target-version = "py313"`, `line-length = 100` e `select = ["E", "W", "F", "I", "B", "UP", "S", "ANN", "N"]`. `ANN202`, retorno de função privada, fica fora, porque RNF-11 fala em funções públicas. Em `tests/**`, ficam fora `S101` (`assert`) e `ANN`. `ruff format` com as opções padrão.
- **Justificativa:** RNF-11 exige *type hints* em funções públicas (família `ANN`); a família `S` inclui `S311`, citada pela ameaça A8 de docs/04; `I` e `UP` mantêm importações e sintaxe modernas.
- **Alternativas:** `flake8` + `black` + `isort` (três ferramentas em vez de uma); selecionar `ALL` (ruído alto e regras conflitantes).

## R18. Regra de dependência entre camadas

- **Decisão:** `tests/unit/test_architecture.py` percorre com `ast` os módulos de `src/cofre` e falha se:
  - `core` importar qualquer outra camada;
  - `repositories` importar `services` ou `api`;
  - `services` importar `api`, `fastapi` ou `starlette`.
- **Justificativa:** princípio IV e docs/03 §2.2; é barato e impede regressões nas unidades seguintes, que acrescentam `crypto` à mesma verificação.
- **Alternativas:** `import-linter` (dependência a mais para cinco regras); revisão manual (não é executável).

## R19. Rotas de diagnóstico só nos testes

- **Decisão:** `tests/support/probe.py` define um `APIRouter` com `POST /api/v1/_probe/echo` (corpo Pydantic com um campo obrigatório) e `GET /api/v1/_probe/boom` (lança `RuntimeError` com um valor marcador na mensagem). A fixture `app` o inclui na aplicação criada por `create_app`.
- **Justificativa:** 422 e 500 precisam de rotas que aceitem corpo e que falhem, e a unidade 001 não tem nenhuma. Registrá-las só na suíte evita expor endpoints de diagnóstico em produção (princípio V e docs/04).
- **Alternativas:** rota de diagnóstico condicionada a `COFRE_ENV` (superfície a mais em produção se a variável for mal configurada); esperar a unidade 002 (deixa FR-007 e FR-008 sem teste).

## R20. Relatório de execução do incremento

- **Decisão:** ao fim da Fase B, rodar `docker compose run --rm tests`, preencher `docs/relatorios/AAAA-MM-DD-incremento-1.md` com o modelo de `docs/relatorios/README.md` a partir de `reports/`, e apontar a seção *Evidências de execução* do README para ele.
- **Justificativa:** docs/07 §6 e a Definição de Concluído de docs/05 §7.
- **Alternativas:** gerar o relatório automaticamente (YAGNI; o formato é curto e muda pouco).

## R21. Testes de fumaça e do workflow de CI

- **Decisão:**
  - **`tests/smoke/conftest.py`:** *fixture* de sessão `compose_stack` que executa `docker compose -p cofre-smoke up -d --build --wait api`, entrega `http://localhost:8000` e, no encerramento, executa `docker compose -p cofre-smoke down -v`. Se o Docker não estiver disponível, a *fixture* **falha**, sem pular o teste, para não produzir falso verde.
  - **`tests/smoke/test_compose_stack.py`** (`smoke`), um teste por verificação:
    - `/health` responde 200 e `/docs` responde 200;
    - `docker compose -p cofre-smoke exec -T api id -u` não é `0`;
    - após `docker compose -p cofre-smoke restart api`, `test -f /data/cofre.db` continua verdadeiro;
    - `docker compose -p cofre-smoke run --rm tests pytest tests/unit/test_clock.py --no-cov` grava `reports/junit.xml` no host.
  - **`tests/unit/test_ci_workflow.py`** (`unit`): lê `.github/workflows/ci.yml` com `pyyaml` e verifica:
    - gatilhos `pull_request` e `push` para `develop` e `main`;
    - jobs `lint`, `test` e `docker`, com `needs` em cadeia;
    - comandos obrigatórios: `uv lock --check`, `ruff check`, `ruff format --check`, `pytest`, `pytest -m smoke` e `docker compose run --rm tests`;
    - `upload-artifact` de `reports` com `if: always()`.
- **Justificativa:** o princípio III exige que os cenários da US4 sejam testes automatizados com `req`. O nome de projeto `cofre-smoke` isola containers e volume do ambiente de desenvolvimento, de modo que `down -v` não apaga o banco local. docs/07 §2 já define o nível `smoke` com base em `docker compose`.
- **Alternativas:**
  - asserções em *shell* dentro do workflow: não têm marcador `req` e não rodam localmente;
  - teste de fumaça só com HTTP: não verifica UID nem persistência;
  - validar o workflow só pela execução no GitHub: a regressão só aparece depois do push.
