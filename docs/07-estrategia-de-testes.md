# 07 — Estratégia de Testes e Harness de Validação

> **Status:** Aprovado · **Versão:** 1.0.0 · **Última revisão:** 2026-09-13
> O harness é construído na unidade 001 ([09-roadmap.md](09-roadmap.md)). Este documento define **o que** ele precisa garantir; o `plan.md` da unidade 001 define os detalhes de implementação.

## 1. Objetivos

1. **Provar a spec:** todo cenário de aceitação e todo caso de borda das specs vira um teste automatizado.
2. **Proteger as garantias de segurança** de [04-seguranca.md](04-seguranca.md) com testes dedicados, que falham se alguém quebrar a criptografia, o isolamento ou a higiene de logs.
3. **Gerar evidências** de execução versionadas e rastreáveis até os requisitos.

## 2. Níveis de teste

| Nível | Diretório | Marcador | Escopo | Base |
|-------|-----------|----------|--------|------|
| Unitário | `tests/unit/` | `unit` | `crypto`, gerador, avaliador de força, *services* com repositórios falsos. | `pytest` |
| Integração | `tests/integration/` | `integration` | *Repositories* e *services* sobre SQLite temporário. | `pytest` + SQLAlchemy |
| API / contrato | `tests/api/` | `api` | Endpoints via HTTP em memória; status, corpo e formato de erro validados contra os contratos em `specs/NNN-*/contracts/`. | `TestClient` (httpx) |
| Segurança | `tests/security/` | `security` | Garantias de RNF-01 a RNF-06: nada em claro no banco, nada sensível em logs, IDOR, expiração e revogação de sessão, adulteração de dados cifrados. | `pytest` + `caplog` |
| Fumaça | `tests/smoke/` | `smoke` | O container sobe e `/health` responde. *(Could)* | `docker compose` |

**Pirâmide esperada:** maioria unitária, forte camada de API (onde vivem os cenários de aceitação) e poucos testes de fumaça.

## 3. Harness

### 3.1 Base

- `pytest`, `pytest-cov` e configuração centralizada em `pyproject.toml` (`testpaths`, marcadores registrados, `--strict-markers`).
- **Relógio controlável** (`FakeClock`) injetado na aplicação: expiração de sessão e bloqueio de login são testados avançando o relógio, nunca com `sleep`.
- **Parâmetros de Argon2id reduzidos** apenas com `COFRE_ENV=test`, para a suíte rodar em segundos.
- **Isolamento total:** banco novo por teste, nenhuma dependência de ordem, nenhum acesso à rede externa.

### 3.2 Fixtures planejadas (`tests/conftest.py`)

| Fixture | Fornece |
|---------|---------|
| `settings` | Configuração de teste: `COFRE_ENV=test`, Argon2id reduzido, SQLite em `tmp_path`. |
| `clock` | `FakeClock` com `advance(minutes=...)`. |
| `app`, `client` | Aplicação criada por `create_app(settings, clock)` e `TestClient`. |
| `make_user` | Cadastra um usuário e devolve e-mail e senha mestra. |
| `auth_client` | Cliente HTTP já autenticado com um token válido. |
| `auth_client_factory` | Cria quantos clientes autenticados forem necessários, cada um com um usuário diferente (testes de isolamento, RNF-03). |
| `make_credential` | Cria credenciais via API para o usuário do `auth_client`. |
| `raw_database` | Acesso direto ao arquivo SQLite, para os testes de segurança inspecionarem bytes armazenados. |

### 3.3 Marcador de rastreabilidade

Todo teste de aceitação ou de borda declara os requisitos que verifica:

```python
@pytest.mark.api
@pytest.mark.req("RF-11", "RNF-03")
def test_user_cannot_read_credential_owned_by_another_user(auth_client_factory):
    alice, bob = auth_client_factory(), auth_client_factory()
    credential = alice.post("/api/v1/credentials", json={"title": "Banco", "password": "x"}).json()

    response = bob.get(f"/api/v1/credentials/{credential['id']}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

Um *hook* do harness valida o formato dos IDs (`RF-\d{2}`, `RNF-\d{2}`, `RN-\d{2}`) e gera `reports/rastreabilidade.md`, com os testes de cada requisito e os requisitos *Must* sem teste.

## 4. Catálogo inicial de casos de borda

Toda spec deve incluir, na seção *Edge Cases*, ao menos os casos aplicáveis desta lista.

### Unidade 002 — Contas e sessões

| Caso | Esperado | Ref. |
|------|----------|------|
| Cadastro com `Ana@Email.com ` e depois com `ana@email.com` | Segundo cadastro → 409 | RN-01 |
| Senha mestra com 11 / 12 / 128 / 129 caracteres | 422 / 201 / 201 / 422 | RN-02 |
| Senha mestra com acentos e emoji | Aceita; login funciona com a mesma string | RN-02 |
| Senha mestra que contém o e-mail | 422 | RN-02 |
| Login com e-mail inexistente vs. senha errada | Mesmo status, `code` e mensagem | RN-04 |
| 5 falhas seguidas e depois a senha correta | 429 com `Retry-After`; após 15 min (relógio) → 201 | RN-14 |
| 5 falhas seguidas com e-mail **não cadastrado** | 6ª tentativa → 429 com `Retry-After`, idêntico ao de um e-mail cadastrado | RN-04, RN-14 |
| Falhas intercaladas com um login bem-sucedido | Contador zera; sem bloqueio | RN-14 |
| Token ausente, malformado, expirado (31 min), após logout, após troca de senha mestra | 401 `UNAUTHENTICATED` | RN-05 |
| Troca de senha mestra | Credenciais continuam legíveis com a nova senha; senha antiga → 401 | RF-06 |

### Unidade 003 — Cofre de credenciais

| Caso | Esperado | Ref. |
|------|----------|------|
| `title` só com espaços; `title` com 100 / 101 caracteres | 422 / 201 / 422 | RN-06 |
| `password` com 1024 / 1025; `notes` com 10.000 / 10.001 | 201 / 422 | RN-06 |
| `url` = `javascript:alert(1)` ou `ftp://x` | 422 | RN-06 |
| `PATCH` com corpo vazio ou tentando anular `title`/`password` | 422 | RF-12 |
| ID que não é UUID / UUID inexistente / credencial de outro usuário | 422 / 404 / 404 | RNF-03 |
| Criação da credencial nº 1.001 | 409 `VAULT_LIMIT_REACHED` | RN-07 |
| `limit` = 0 ou 101; `offset` além do total | 422; lista vazia com `total` correto | RN-13 |
| Busca com caixa diferente do título | Encontra | RN-15 |
| Qualquer item da listagem ou da busca | Não contém o campo `password` | RN-08 |

### Unidade 004 — Gerador e avaliador

| Caso | Esperado | Ref. |
|------|----------|------|
| Comprimento 7 / 8 / 128 / 129 | 422 / 200 / 200 / 422 | RN-10 |
| Todos os conjuntos desativados | 422 | RN-10 |
| Comprimento 3 com 4 conjuntos | 422 | RN-10 |
| 1.000 gerações com `exclude_ambiguous` | Nenhum caractere ambíguo | RN-10 |
| 1.000 gerações | Todo conjunto selecionado presente em cada senha | RN-10 |
| Senha vazia ou acima do limite definido na spec | 422 | RF-15 |

### Transversais de segurança

| Caso | Esperado | Ref. |
|------|----------|------|
| Após criar credenciais com valores marcadores, procurar esses valores nos bytes do arquivo SQLite | Nenhuma ocorrência | RNF-01 |
| Capturar todos os logs de um fluxo completo (cadastro → login → CRUD → logout) | Nenhuma senha, senha mestra ou token nos logs | RNF-04 |
| Alterar um byte do `ciphertext` ou trocar `ciphertext` entre duas credenciais | Erro de integridade; nenhum dado retornado | RNF-01 |
| 10.000 cifragens com a mesma chave | Nenhum nonce repetido | RNF-05 |
| Aplicação iniciada com Argon2id abaixo do mínimo fora de `COFRE_ENV=test` | Falha na inicialização | RNF-02 |

## 5. Execução

Disponível a partir do incremento 1:

```bash
uv run pytest                          # suíte completa com gate de cobertura
uv run pytest -m unit                  # somente unitários
uv run pytest -m "api or security"     # aceitação e segurança
docker compose run --rm tests          # suíte em container (reprodutível)
```

**Gate de qualidade:** `--cov=cofre --cov-branch --cov-fail-under=85`, mais `ruff check` e `ruff format --check`.

## 6. Relatórios e evidências

**Artefatos de cada execução** (pasta `reports/`, ignorada pelo Git e publicada como artefato no CI):

| Arquivo | Conteúdo |
|---------|----------|
| `reports/pytest-output.log` | Saída completa do pytest |
| `reports/junit.xml` | Resultados em JUnit XML |
| `reports/coverage.xml` e `reports/htmlcov/` | Cobertura |
| `reports/rastreabilidade.md` | Requisito → testes |

**Evidências versionadas** ([`docs/relatorios/`](relatorios/)): ao concluir cada incremento, é publicado um relatório `AAAA-MM-DD-incremento-N.md` no formato definido em [docs/relatorios/README.md](relatorios/README.md). A seção *Evidências de testes* do [README](../README.md) aponta para o relatório mais recente.

## 7. Integração contínua

Workflow `.github/workflows/ci.yml` (incremento 1):

| Gatilho | Jobs |
|---------|------|
| PR para `develop` ou `main`; push em `develop` ou `main` | `lint` (ruff) → `test` (pytest com gate e upload de `reports/`) → `docker` (build da imagem) |

PRs só podem ser mergeados com o CI verde.
