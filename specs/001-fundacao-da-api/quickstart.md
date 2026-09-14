# Quickstart: Fundação da API

**Spec**: [spec.md](spec.md) · **Contrato**: [contracts/openapi.yaml](contracts/openapi.yaml) · **Dados**: [data-model.md](data-model.md)

Roteiro de validação ponta a ponta da unidade 001, para ser executado ao fim da Fase B e registrado no relatório de execução do incremento 1. Cada cenário indica os requisitos que verifica.

Os comandos estão em sintaxe POSIX. No PowerShell, troque `\` de fim de linha por `` ` `` e defina variáveis com `$env:NOME = "valor"`.

## Pré-requisitos

- Git, Docker com Compose v2.
- Para os cenários sem Docker: Python 3.13 e `uv` (docs/08 §1).
- Clone limpo na branch `develop` com a Fase B da unidade 001 mergeada.

## 1. API com Docker (RF-01, RNF-08, RNF-10)

```bash
docker compose up --build -d
curl -i http://localhost:8000/health
```

**Esperado:**

- `HTTP/1.1 200`, corpo `{"status":"ok"}` e cabeçalho `x-request-id` com um UUID;
- `http://localhost:8000/docs` abre a Swagger UI, e `/openapi.json` descreve `GET /health`;
- `docker compose exec api id -u` imprime `10001`, ou seja, não-root.

## 2. Persistência do volume (RNF-10)

```bash
docker compose exec api ls -l /data
docker compose down
docker compose up -d
docker compose exec api ls -l /data
```

**Esperado:** o arquivo `cofre.db` continua existindo após o `down` sem `-v`.

## 3. Contrato de erros e cabeçalhos (RNF-04, RNF-08, RNF-14)

```bash
curl -i http://localhost:8000/api/v1/inexistente
curl -i -X POST http://localhost:8000/health
curl -i -H "X-Request-ID: meu-id-123" http://localhost:8000/health
curl -i -H "X-Request-ID: id com espaço" http://localhost:8000/health
```

**Esperado:**

| Chamada | Status | Verificar |
|---------|--------|-----------|
| `/api/v1/inexistente` | 404 | `error.code` = `NOT_FOUND`; `cache-control: no-store`; `x-request-id` presente. |
| `POST /health` | 405 | `error.code` = `METHOD_NOT_ALLOWED`; cabeçalho `allow: GET`. |
| `X-Request-ID: meu-id-123` | 200 | `x-request-id: meu-id-123`. |
| `X-Request-ID` com espaço | 200 | `x-request-id` é um UUID novo, diferente do enviado. |

## 4. Logs sem dados sensíveis (RNF-04, RNF-13)

```bash
curl -s -H "Authorization: Bearer MARCADOR-TOKEN" \
  "http://localhost:8000/api/v1/inexistente?q=MARCADOR-QUERY" > /dev/null
docker compose logs api | tail -n 5
docker compose logs api | grep -c MARCADOR
```

**Esperado:** a última linha do log é um JSON com `event` = `request`, `route` = `null`, `status` = `404` e `duration_ms`. A contagem de `MARCADOR` é `0`.

## 5. Suíte em container e artefatos (RNF-09, RNF-10)

```bash
docker compose run --rm tests
ls reports
```

**Esperado:**

- a suíte termina com sucesso e cobertura total ≥ 85%;
- `reports/` contém `pytest-output.log`, `junit.xml`, `coverage.xml`, `htmlcov/` e `rastreabilidade.md`;
- `rastreabilidade.md` lista testes para RF-01, RNF-08, RNF-09, RNF-10, RNF-11, RNF-13, RNF-14 e RNF-15, e a seção "Requisitos Must sem teste" não cita nenhum deles.

Ao terminar: `docker compose down -v`.

## 6. Teste de fumaça (RNF-10)

Com a porta 8000 livre, ou seja, depois do `docker compose down` do cenário 5:

```bash
uv sync
uv run pytest -m smoke --no-cov
docker compose -p cofre-smoke ps
```

**Esperado:** os testes `smoke` passam (`/health`, `/docs`, UID não-root, persistência do volume e `reports/` gravado pelo serviço `tests`), e o último comando não lista containers, porque a stack `cofre-smoke` é removida ao final.

## 7. Sem Docker, inclusive no Windows (RNF-15)

```bash
uv sync
uv run pytest
uv run pytest -m unit
uv run uvicorn cofre.main:create_app --factory --no-access-log
```

**Esperado:**

- `uv run pytest` passa com o gate de cobertura;
- `uv run pytest -m unit` passa **sem** aplicar o gate e ainda gera os relatórios;
- o servidor sobe em `http://127.0.0.1:8000`, cria `./data/cofre.db` e `/health` responde 200.

## 8. Banco indisponível e recuperação (RF-01)

```bash
mkdir -p /tmp/cofre-bloqueado
COFRE_DATABASE_URL=sqlite:////tmp/cofre-bloqueado uv run uvicorn cofre.main:create_app --factory
curl -i http://127.0.0.1:8000/health
```

**Esperado:** a aplicação sobe e `/health` responde 503 com `error.code` = `SERVICE_UNAVAILABLE`, sem caminho nem texto de exceção no corpo. O cenário de recuperação sem reinício é coberto por `tests/api/test_health.py`.

## 9. Configuração insegura (RNF-02, RNF-10)

```bash
COFRE_ENV=production COFRE_ARGON2_MEMORY_KIB=1024 \
  uv run uvicorn cofre.main:create_app --factory
COFRE_ENV=staging uv run uvicorn cofre.main:create_app --factory
```

**Esperado:** nos dois casos, o processo termina com erro, a mensagem cita `COFRE_ARGON2_MEMORY_KIB` ou `COFRE_ENV`, e o valor recebido (`1024`, `staging`) não aparece.

## 10. Qualidade e CI (RNF-10, RNF-11)

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
```

**Esperado:** os três comandos terminam sem erros. No GitHub, o PR de implementação mostra os jobs `lint`, `test` e `docker` verdes e o artefato `reports` no job `test`.
