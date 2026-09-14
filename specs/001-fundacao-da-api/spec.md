# Feature Specification: Fundação da API

**Feature Branch**: `spec/001-fundacao-da-api`

**Created**: 2026-09-13

**Status**: Aprovada

**Versão**: 1.0.0

**Input**: User description: "Unidade 001 — Fundação da API. Escopo: RF-01 e RNF-08 a RNF-11 e RNF-13 a RNF-15. Inclui `/health` 200/503, formato de erro padronizado (docs/03 §6.3), `Cache-Control: no-store`, `X-Request-ID` validado, fábrica `create_app(settings=None, clock=None)`, `Settings` `COFRE_*`, harness de testes (fixtures, marcador `req`, relatório de rastreabilidade, gate de 85% de linhas e ramificações, níveis `perf`/`smoke` fora do padrão), Docker/compose, CI e relatório de execução. Inclua os casos de borda da unidade 001 e os transversais aplicáveis de docs/07 §4."

<!--
  Cofre: override de .specify/templates/overrides/ (docs/05-processo-sdd.md §8).
  - Escreva o conteúdo em pt-BR e mantenha os títulos de seção em inglês.
  - Status: Rascunho · Em revisão · Aprovada · Implementada · Revisada.
  - Feature Branch: spec/NNN-slug (Fase A). O projeto não usa a extensão git do Spec Kit.
  - Respeite .specify/memory/constitution.md e docs/04-seguranca.md (normativo).
-->

## Contexto da unidade

A unidade 001 não entrega funcionalidade de cofre. Ela entrega a **base sobre a qual as unidades 002 a 005 são construídas e verificadas**: uma aplicação que sobe de forma reprodutível, responde a verificações de saúde, fala um contrato HTTP uniforme (erros, cabeçalhos e identificação de requisição) e vem acompanhada de um harness de testes que prova, com rastreabilidade até os requisitos, que a especificação foi cumprida.

**Atores:**

- **Orquestrador/operador**: sistema ou pessoa que precisa saber se a API está apta a receber tráfego.
- **Cliente da API**: qualquer consumidor HTTP, inclusive a Swagger UI.
- **Mantenedor/avaliador**: quem clona o repositório, sobe o ambiente, roda a suíte e lê as evidências.
- **Pipeline de CI**: automação que bloqueia mudanças que quebram lint, testes ou a imagem.

Por ser uma unidade de fundação, algumas decisões técnicas já fixadas em `docs/` e nos ADRs aparecem nos requisitos (nome da fábrica, prefixo das variáveis, comandos). Elas são parte do contrato do projeto, não escolhas desta spec.

## Clarifications

### Session 2026-09-13

Perguntas levantadas pelo `/speckit-clarify` e respondidas a partir da documentação do projeto (nenhuma exigiu decisão de produto do mantenedor):

- Q: Qual status e `code` a API devolve para um método HTTP não suportado numa rota existente (ex.: `POST /health`)? → A: **405** com `code` `METHOD_NOT_ALLOWED`, no formato padronizado. O catálogo de docs/03 §6.3 não tinha esse caso; RNF-08 exige o formato padronizado para todo erro, então o código foi acrescentado a docs/03 (R-022).
- Q: "Letras" no padrão do `X-Request-ID` inclui letras Unicode? → A: Não. Apenas ASCII `A–Z`, `a–z`, `0–9` e `-`, de 1 a 64 caracteres. O objetivo declarado em docs/03 §6.2 é impedir injeção de conteúdo nos logs; letras Unicode reabririam caracteres de controle e homóglifos.
- Q: O campo de rota do log registra o caminho bruto da requisição? → A: Não. Registra o **modelo de rota** (ex.: `/api/v1/credentials/{id}`) quando há rota correspondente e fica nulo quando não há; a *query string* nunca é registrada. Caminhos brutos e parâmetros podem carregar identificadores e termos de busca (RNF-04, docs/04 §5 regra 2).
- Q: `Cache-Control: no-store` vale só para respostas de sucesso de `/api/v1`? → A: Vale para **toda** resposta cujo caminho comece por `/api/v1`, inclusive erros 404, 405, 422 e 500 (docs/03 §6.2, ameaça A9). `/health`, `/docs` e `/openapi.json` não são obrigados a enviá-lo.
- Q: A aplicação deve recusar iniciar se o banco estiver indisponível? → A: Não. A aplicação inicia e `/health` responde 503 enquanto o banco não responder, voltando a 200 quando ele se recuperar. Recusar a inicialização impediria o orquestrador de observar o estado pelo `/health` (RF-01).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificação de saúde da API (Priority: P1)

O orquestrador consulta `/health` periodicamente para decidir se envia tráfego à API. A resposta indica apenas se a aplicação e o banco estão operacionais, sem revelar detalhes internos.

**Why this priority**: RF-01 é o único requisito funcional da unidade e o critério de conclusão do incremento 1. Sem ele não há como verificar o container nem fazer o teste de fumaça.

**Independent Test**: Criar a aplicação com banco em diretório temporário, chamar `GET /health` e verificar 200; repetir apontando o banco para um local inacessível e verificar 503.

**Acceptance Scenarios**:

1. **Given** a aplicação em execução com o banco acessível, **When** o cliente faz `GET /health` sem autenticação, **Then** recebe **200** com o corpo exato `{"status": "ok"}`.
2. **Given** a aplicação em execução com o banco inacessível, **When** o cliente faz `GET /health`, **Then** recebe **503** com `error.code` = `SERVICE_UNAVAILABLE`, `message` em pt-BR e nenhum detalhe interno (caminho do banco, nome do driver, versões, texto de exceção).
3. **Given** o banco estava inacessível e `/health` respondeu 503, **When** o banco volta a ficar acessível e o cliente chama `/health` de novo, **Then** recebe 200, sem reiniciar a aplicação.
4. **Given** o banco inacessível no momento em que a aplicação é iniciada, **When** a aplicação sobe, **Then** ela inicia normalmente e `/health` responde 503.

---

### User Story 2 - Contrato HTTP uniforme: erros e cabeçalhos (Priority: P1)

O cliente da API recebe sempre o mesmo formato de erro, com `code` estável em inglês e mensagem em pt-BR, consulta a especificação OpenAPI publicada e tem a garantia de que respostas de `/api/v1` não são guardadas em cache.

**Why this priority**: RNF-08 (Must) e RNF-14 são o contrato que todas as unidades seguintes herdam. Definido agora, os testes de contrato das unidades 002 a 005 só acrescentam casos.

**Independent Test**: Com a aplicação de teste, chamar uma rota inexistente sob `/api/v1`, um método não suportado em `/health`, uma rota de teste que exige corpo JSON (com JSON malformado) e uma rota de teste que lança exceção; validar status, corpo contra o contrato e cabeçalhos.

**Acceptance Scenarios**:

1. **Given** a aplicação em execução, **When** o cliente chama `GET /api/v1/rota-inexistente`, **Then** recebe **404** com `error.code` = `NOT_FOUND`, `message` em pt-BR e `Cache-Control: no-store`.
2. **Given** uma rota que aceita corpo JSON, **When** o cliente envia um corpo que não é JSON válido, **Then** recebe **422** com `error.code` = `VALIDATION_ERROR` e `details` com ao menos um item `{field, issue}` em pt-BR.
3. **Given** uma rota que falha com erro inesperado, **When** o cliente a chama, **Then** recebe **500** com `error.code` = `INTERNAL_ERROR`, sem *stack trace*, mensagem da exceção ou nome de classe interna no corpo.
4. **Given** a aplicação em execução, **When** o cliente chama `POST /health`, **Then** recebe **405** com `error.code` = `METHOD_NOT_ALLOWED`.
5. **Given** a aplicação em execução, **When** o cliente acessa `/openapi.json` e `/docs`, **Then** obtém uma especificação OpenAPI 3 válida que descreve `/health` e o esquema de erro, e a Swagger UI correspondente.

---

### User Story 3 - Harness de testes rastreável com gate de qualidade (Priority: P1)

O mantenedor roda a suíte com um único comando e obtém, além do resultado, a cobertura de linhas e ramificações, o relatório JUnit, o log completo e um relatório que liga cada requisito aos testes que o verificam. Se a cobertura cair abaixo de 85% ou um teste declarar um requisito inexistente, a execução falha.

**Why this priority**: RNF-09 (Must) e o princípio III da constituição. Todas as unidades seguintes dependem desse harness para provar a própria spec.

**Independent Test**: Rodar a suíte padrão e verificar os artefatos em `reports/`; rodar os testes de autoverificação do harness, que executam suítes de exemplo isoladas (marcador inválido, ID inexistente, cobertura abaixo do limite) e conferem o resultado.

**Acceptance Scenarios**:

1. **Given** o repositório com dependências instaladas, **When** o mantenedor executa `uv run pytest`, **Then** a suíte padrão roda sem os níveis `perf` e `smoke`, aplica o gate de cobertura e gera `reports/pytest-output.log`, `reports/junit.xml`, `reports/coverage.xml`, `reports/htmlcov/` e `reports/rastreabilidade.md`.
2. **Given** um teste marcado com `@pytest.mark.req("RF-01")`, **When** a suíte roda, **Then** `reports/rastreabilidade.md` lista esse teste sob RF-01.
3. **Given** um teste marcado com um ID fora do formato (`@pytest.mark.req("RF-1")`) ou inexistente em docs/02 (`@pytest.mark.req("RF-99")`), **When** a suíte é coletada, **Then** a execução falha com erro que identifica o teste e o ID.
4. **Given** uma execução da seleção padrão com cobertura de linhas e ramificações abaixo de 85% no pacote `cofre`, **When** a suíte termina, **Then** a execução é marcada como falha mesmo que todos os testes passem.
5. **Given** um teste que usa um marcador não registrado, **When** a suíte é coletada, **Then** a execução falha (`--strict-markers`).
6. **Given** requisitos *Must* de docs/02 sem nenhum teste marcado, **When** a suíte roda, **Then** `reports/rastreabilidade.md` os lista na seção "Requisitos Must sem teste", sem falhar a execução.

---

### User Story 4 - Ambiente reprodutível e integração contínua (Priority: P2)

O avaliador clona o repositório e, com Docker, sobe a API e roda a suíte com um comando cada. Quem prefere não usar Docker faz o mesmo com `uv` em Windows, macOS ou Linux. Todo PR para `develop` ou `main` passa por lint, testes e build da imagem no CI.

**Why this priority**: RNF-10 e RNF-11 são *Must* e fazem parte do critério de conclusão do incremento 1, mas dependem das histórias 1 a 3 para ter o que empacotar e verificar.

**Independent Test**: Rodar os testes `smoke`, que sobem a stack com Docker Compose num projeto isolado e verificam API, volume e serviço de testes, e o teste que valida a estrutura do workflow de CI. A execução real dos três jobs aparece no PR de implementação.

**Acceptance Scenarios**:

1. **Given** um clone limpo e Docker instalado, **When** a stack sobe com `docker compose up --build`, **Then** a API responde em `http://localhost:8000/health` com 200 e serve a Swagger UI em `/docs`, com o processo rodando com UID diferente de 0.
2. **Given** um clone limpo e Docker instalado, **When** o avaliador executa `docker compose run --rm tests`, **Then** a suíte roda no container e os artefatos aparecem em `./reports` no host.
3. **Given** a API em execução com o banco criado no volume `cofre-data`, **When** o container da API é reiniciado, **Then** o arquivo do banco continua existindo no volume.
4. **Given** o workflow de CI do repositório, **When** ele é avaliado para PRs e pushes em `develop` e `main`, **Then** executa, nesta ordem, `lint` (`ruff check`, `ruff format --check` e verificação do lock), `test` (suíte padrão com gate e publicação de `reports/` mesmo em falha) e `docker` (build, testes de fumaça e suíte no container), e a falha de qualquer job marca o check do PR como falho.

---

### User Story 5 - Configuração e inicialização seguras (Priority: P2)

O operador configura a aplicação só por variáveis de ambiente `COFRE_*`. Valores inválidos ou inseguros impedem a inicialização com uma mensagem clara. Os testes criam aplicações isoladas passando configuração e relógio próprios.

**Why this priority**: Viabiliza testes determinísticos (RNF-09) e protege a produção de parâmetros criptográficos fracos (docs/04 §5 regra 6) antes de a unidade 002 usá-los.

**Independent Test**: Criar aplicações com `Settings` e relógio de teste explícitos; tentar criar `Settings` com valores inválidos e com Argon2id abaixo do mínimo em cada `COFRE_ENV`.

**Acceptance Scenarios**:

1. **Given** nenhuma variável `COFRE_*` definida, **When** a aplicação é criada sem argumentos, **Then** usa os padrões de docs/08 §3 e o relógio do sistema.
2. **Given** `COFRE_ENV=production` e `COFRE_ARGON2_MEMORY_KIB=1024`, **When** a aplicação é iniciada, **Then** a inicialização falha com mensagem que identifica a variável.
3. **Given** `COFRE_ENV=test` e parâmetros de Argon2id reduzidos, **When** a aplicação é criada, **Then** ela inicia normalmente.
4. **Given** uma configuração e um relógio de teste passados à fábrica, **When** a aplicação registra uma requisição, **Then** o instante do log vem do relógio de teste.
5. **Given** o módulo da aplicação importado com variáveis `COFRE_*` inválidas no ambiente, **When** nenhuma aplicação é criada, **Then** a importação não falha, porque nada é lido do ambiente na importação.

---

### User Story 6 - Identificação e registro de requisições (Priority: P3)

O operador correlaciona uma resposta com o registro de log pelo `X-Request-ID`. Cada requisição gera uma linha de log JSON com identificador, método, rota, status e duração, e nunca dados sensíveis.

**Why this priority**: RNF-13 é *Could*; a propagação segura do `X-Request-ID` (casos de borda de docs/07 §4) e a higiene de logs (RNF-04) são as partes que protegem as unidades seguintes.

**Independent Test**: Enviar requisições com `X-Request-ID` válido, inválido e ausente, capturar os logs e verificar cabeçalho, campos do log e ausência dos valores rejeitados e de dados sensíveis.

**Acceptance Scenarios**:

1. **Given** uma requisição com `X-Request-ID: abc-123`, **When** a resposta é enviada, **Then** ela contém `X-Request-ID: abc-123` e o log da requisição registra `request_id` = `abc-123`.
2. **Given** uma requisição sem `X-Request-ID`, **When** a resposta é enviada, **Then** ela contém um `X-Request-ID` com um UUID v4 novo, igual ao `request_id` do log.
3. **Given** uma requisição qualquer, **When** ela termina, **Then** é emitida exatamente uma linha de log JSON com `timestamp`, `level`, `event`, `request_id`, `method`, `route`, `status` e `duration_ms`.
4. **Given** uma requisição com cabeçalho `Authorization`, cabeçalho `Cookie`, *query string* e corpo contendo valores marcadores, **When** os logs da requisição são capturados, **Then** nenhum dos valores marcadores aparece.

---

### Edge Cases

Casos da unidade 001 em docs/07 §4 (todos obrigatórios):

- `/health` com banco disponível → 200 `{"status": "ok"}`; com banco indisponível → 503 `SERVICE_UNAVAILABLE` (RF-01).
- Rota inexistente → 404 no formato padronizado; JSON malformado → 422 `VALIDATION_ERROR` no formato padronizado (RNF-08, RNF-14).
- Qualquer resposta de `/api/v1` → contém `Cache-Control: no-store` e `X-Request-ID` (RNF-04).
- `X-Request-ID` válido (até 64 caracteres entre letras, dígitos e hífen) → o mesmo valor volta na resposta e é registrado no log (RNF-13).
- `X-Request-ID` com 65 caracteres, com quebra de linha ou com caractere fora do padrão → substituído por um UUID v4 gerado; o valor original não aparece nos logs (RNF-04, RNF-13).

Casos transversais de docs/07 §4 aplicáveis a esta unidade:

- Aplicação iniciada com Argon2id abaixo do mínimo fora de `COFRE_ENV=test` → falha na inicialização (RNF-02). Vale para cada parâmetro isoladamente: memória < 19.456 KiB, iterações < 2, paralelismo < 1.
- Captura de todos os logs de um fluxo → nenhum segredo nos logs (RNF-04). Nesta unidade não há senhas nem tokens de domínio; o caso é verificado com valores marcadores em `Authorization`, `Cookie`, *query string* e corpo.

Os demais transversais (bytes do SQLite, adulteração de `ciphertext`, nonces repetidos) dependem de criptografia e credenciais e ficam para as unidades 002 e 003.

Casos adicionais desta spec:

- `X-Request-ID` com exatamente 64 caracteres válidos → propagado; com valor vazio → UUID v4 gerado (RNF-13).
- `X-Request-ID` com letra acentuada ou outra letra não ASCII (ex.: `ação`) → UUID v4 gerado (RNF-04).
- Dois cabeçalhos `X-Request-ID` na mesma requisição → UUID v4 gerado, porque o valor é ambíguo (RNF-04, RNF-13).
- Método não suportado em rota existente (`POST /health`) → 405 `METHOD_NOT_ALLOWED` (RNF-08, RNF-14).
- Erro inesperado numa rota de `/api/v1` → 500 `INTERNAL_ERROR` com `Cache-Control: no-store` e `X-Request-ID`, e log de nível ERROR sem a mensagem da exceção (RNF-04, RNF-13).
- Erro de validação cujo valor recebido é um marcador → o marcador não aparece em `message` nem em `details` (RNF-04).
- Banco indisponível na inicialização → aplicação sobe e `/health` responde 503; recuperação do banco → 200 sem reiniciar (RF-01).
- `COFRE_ENV` com valor fora de `production`, `development` e `test` → falha na inicialização (RNF-10).
- `COFRE_LOG_LEVEL` inválido; inteiro não positivo em `COFRE_SESSION_TTL_MINUTES`, `COFRE_LOGIN_MAX_ATTEMPTS`, `COFRE_LOGIN_LOCK_MINUTES` ou `COFRE_MAX_CREDENTIALS_PER_USER`; `COFRE_DATABASE_URL` que não seja SQLite → falha na inicialização sem ecoar o valor recebido (RNF-10, RNF-04).
- Duas aplicações criadas no mesmo processo com configurações diferentes → não compartilham banco, relógio nem estado (RNF-09).
- `@pytest.mark.req()` sem argumentos → erro de coleta (RNF-09).
- Suíte executada só com um subconjunto (`-m unit`, `-k`, caminho de arquivo) → relatórios gerados, sem aplicar o gate de cobertura (RNF-09).
- Suíte com testes falhando → `reports/rastreabilidade.md`, `junit.xml` e `pytest-output.log` gerados mesmo assim (RNF-09).
- `uv.lock` desatualizado em relação ao `pyproject.toml` → CI falha no job `lint` (RNF-10).

## Requirements *(mandatory)*

### Functional Requirements

**Verificação de saúde**

- **FR-001**: O sistema DEVE expor `GET /health`, público e fora de `/api/v1`, que responde **200** com o corpo exato `{"status": "ok"}` quando a aplicação e o banco estão operacionais (RF-01, RNF-08).
- **FR-002**: `GET /health` DEVE responder **503** com `code` `SERVICE_UNAVAILABLE` no formato padronizado quando o banco não responde, sem expor caminho ou tipo do banco, versões, nomes internos ou texto de exceção (RF-01, RNF-04, RNF-14).
- **FR-003**: O estado do banco DEVE ser verificado a cada chamada de `/health`, sem cache; a aplicação DEVE iniciar mesmo com o banco indisponível e voltar a responder 200 quando ele se recuperar (RF-01).

**Contrato HTTP**

- **FR-004**: A API DEVE usar JSON UTF-8, ter os recursos de negócio sob o prefixo `/api/v1` e publicar a especificação OpenAPI 3 em `/openapi.json` e a Swagger UI em `/docs` (RNF-08).
- **FR-005**: Toda resposta de erro DEVE seguir o formato `{"error": {"code", "message", "details"?}}` de docs/03 §6.3, com `code` estável em inglês e `message` legível em pt-BR; `details` DEVE aparecer apenas em `VALIDATION_ERROR`, como lista não vazia de `{field, issue}` com `issue` em pt-BR (RNF-08, RNF-14).
- **FR-006**: Rota inexistente DEVE responder **404** `NOT_FOUND`, e método não suportado em rota existente DEVE responder **405** `METHOD_NOT_ALLOWED` (RNF-08, RNF-14).
- **FR-007**: Corpo que não é JSON válido ou que viola o esquema de entrada DEVE responder **422** `VALIDATION_ERROR` (RNF-08, RNF-14).
- **FR-008**: Erro inesperado DEVE responder **500** `INTERNAL_ERROR` sem *stack trace*, mensagem de exceção ou nomes internos no corpo (RNF-04, RNF-14).
- **FR-009**: Mensagens e detalhes de erro NÃO DEVEM repetir valores recebidos na requisição (RNF-04).
- **FR-010**: Toda resposta cujo caminho comece por `/api/v1`, inclusive respostas de erro, DEVE conter `Cache-Control: no-store` (RNF-04, RNF-08).

**Identificação e logs de requisição**

- **FR-011**: Toda resposta, inclusive de `/health`, `/docs`, `/openapi.json` e de erro, DEVE conter o cabeçalho `X-Request-ID` (RNF-13).
- **FR-012**: O `X-Request-ID` recebido DEVE ser propagado apenas quando houver um único cabeçalho cujo valor tenha de 1 a 64 caracteres ASCII entre `A–Z`, `a–z`, `0–9` e `-`; em qualquer outro caso, DEVE ser gerado um UUID v4 novo (RNF-04, RNF-13).
- **FR-013**: Cada requisição DEVE gerar exatamente uma linha de log em JSON com `timestamp` (ISO 8601 em UTC, obtido do relógio injetado), `level`, `event`, `request_id`, `method`, `route` (modelo da rota, ou nulo quando não há rota), `status` e `duration_ms` (RNF-13).
- **FR-014**: Os logs NÃO DEVEM conter corpo de requisição ou de resposta, *query string*, valores de cabeçalhos (inclusive `Authorization` e `Cookie`) nem valores de `X-Request-ID` rejeitados (RNF-04, RNF-13).
- **FR-015**: Um erro inesperado DEVE gerar um log de nível ERROR com `request_id`, tipo da exceção e a pilha de chamadas (arquivo, linha e função), sem a mensagem da exceção (RNF-04, RNF-13).
- **FR-016**: O nível mínimo de log DEVE seguir `COFRE_LOG_LEVEL` (RNF-13).

**Configuração e inicialização**

- **FR-017**: A aplicação DEVE ser montada exclusivamente por `create_app(settings=None, clock=None)`; sem argumentos, a fábrica lê a configuração do ambiente e usa o relógio do sistema, e nada é lido do ambiente na importação dos módulos (RNF-09, RNF-10).
- **FR-018**: A configuração DEVE aceitar todas as variáveis `COFRE_*` de docs/08 §3, com os padrões ali definidos (RNF-10, RNF-15).
- **FR-019**: A inicialização DEVE falhar, com mensagem que identifica a variável e sem ecoar o valor recebido, quando `COFRE_ENV` estiver fora de `production`/`development`/`test`, `COFRE_LOG_LEVEL` for inválido, um limite inteiro não for positivo ou `COFRE_DATABASE_URL` não for uma URL SQLite (RNF-04, RNF-10).
- **FR-020**: Fora de `COFRE_ENV=test`, a inicialização DEVE falhar quando qualquer parâmetro do Argon2id estiver abaixo do mínimo OWASP (memória 19.456 KiB, 2 iterações, paralelismo 1) (RNF-02).
- **FR-021**: O relógio DEVE ser injetável e fornecer o instante atual em UTC; o harness DEVE oferecer um relógio de teste que só avança quando mandado (RNF-09).
- **FR-022**: Aplicações criadas pela fábrica DEVEM ser independentes entre si: banco, relógio e estado não são compartilhados (RNF-09).

**Harness de testes**

- **FR-023**: Um único comando (`uv run pytest`) DEVE executar a suíte padrão, que exclui os níveis `perf` e `smoke` (RNF-09, RNF-10).
- **FR-024**: Os marcadores de nível `unit`, `integration`, `api`, `security`, `perf` e `smoke` e o marcador `req` DEVEM estar registrados, e um marcador não registrado DEVE falhar a execução (RNF-09).
- **FR-025**: O marcador `req` DEVE exigir ao menos um ID, validar o formato (`RF-\d{2}`, `RNF-\d{2}`, `RN-\d{2}`) e a existência do ID em docs/02; violação DEVE falhar a coleta identificando o teste e o ID (RNF-09).
- **FR-026**: Toda execução DEVE gerar `reports/rastreabilidade.md` com, para cada requisito, os testes que o declaram, e a seção "Requisitos Must sem teste", que é informativa e não falha a execução (RNF-09).
- **FR-027**: Na seleção padrão completa, a execução DEVE falhar quando a cobertura de linhas e ramificações do pacote `cofre` ficar abaixo de 85%; execuções de subconjuntos DEVEM gerar os relatórios sem aplicar o gate (RNF-09).
- **FR-028**: Toda execução DEVE gerar `reports/pytest-output.log`, `reports/junit.xml`, `reports/coverage.xml` e `reports/htmlcov/`, inclusive quando há testes falhando (RNF-09).
- **FR-029**: O harness DEVE fornecer as fixtures `settings`, `clock`, `app` e `client`, com banco isolado em diretório temporário por teste, sem acesso à rede externa e sem dependência de ordem entre testes (RNF-09).
- **FR-030**: Os testes de API DEVEM validar status, cabeçalhos e corpo das respostas contra `specs/001-fundacao-da-api/contracts/openapi.yaml` (RNF-08).
- **FR-031**: Todo cenário de aceitação e todo caso de borda desta spec DEVE ter ao menos um teste marcado com `@pytest.mark.req` e os IDs correspondentes (RNF-09).

**Ambiente e integração contínua**

- **FR-032**: `docker compose up` DEVE subir a API na porta 8000, com o processo como usuário não-root e o banco SQLite no volume `cofre-data` (RNF-10, RNF-15).
- **FR-033**: `docker compose run --rm tests` DEVE executar a suíte padrão em container e gravar os artefatos em `./reports` no host (RNF-10).
- **FR-034**: As dependências DEVEM estar travadas em `uv.lock`; a imagem DEVE instalar exatamente as versões do lock, e o CI DEVE falhar se o lock estiver desatualizado em relação ao `pyproject.toml` (RNF-10).
- **FR-035**: Sem Docker, `uv sync` seguido de `uv run pytest` ou do servidor com a fábrica DEVE funcionar com Python 3.13 em Windows, macOS e Linux (RNF-15).
- **FR-036**: Os testes de fumaça (marcador `smoke`) DEVEM subir a stack com Docker Compose num projeto isolado do ambiente de desenvolvimento e verificar: `/health` com 200, `/docs` disponível, processo da API com UID diferente de 0, arquivo do banco preservado após reiniciar a API e artefatos gravados em `./reports` pelo serviço `tests` (RNF-10, RNF-15).
- **FR-037**: O CI DEVE rodar em PRs e pushes para `develop` e `main` com os jobs `lint` (`ruff check`, `ruff format --check` e verificação do lock), `test` (suíte padrão com gate e publicação de `reports/` mesmo em falha) e `docker` (build da imagem, testes de fumaça e suíte no container); a estrutura do workflow (gatilhos, jobs, ordem e passos obrigatórios) DEVE ser verificada por teste automatizado (RNF-10, RNF-11).
- **FR-038**: A configuração do `ruff` DEVE exigir *type hints* em funções públicas do pacote `cofre` e proibir o módulo `random` para valores de segurança (regra `S311`) (RNF-05, RNF-11).
- **FR-039**: Ao concluir a Fase B, um relatório de execução do incremento 1 DEVE ser publicado em `docs/relatorios/` no modelo definido, e a seção de evidências do README DEVE apontar para ele (RNF-09).

### Key Entities *(include if feature involves data)*

Esta unidade não cria tabelas de domínio. As entidades são estruturas de configuração, contrato e evidência:

- **Configuração (Settings)**: conjunto das variáveis `COFRE_*` com padrões e validações; imutável depois de criada.
- **Relógio (Clock)**: fonte do instante atual em UTC; tem uma variante de sistema e uma de teste, que só avança quando mandado.
- **Resposta de erro**: objeto `error` com `code`, `message` e `details` opcional (lista de `field` e `issue`).
- **Estado de saúde**: resultado da verificação (`ok` ou indisponível), traduzido em 200 ou 503.
- **Contexto de requisição**: identificador (`request_id`), método, modelo de rota, status e duração de uma requisição.
- **Registro de log de requisição**: linha JSON derivada do contexto de requisição.
- **Catálogo de requisitos**: IDs e prioridades lidos de docs/02, usados para validar o marcador `req`.
- **Relatório de rastreabilidade**: mapa requisito → testes e lista de requisitos *Must* sem teste.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir de um clone limpo, a API fica disponível e a suíte roda com **um comando cada** (`docker compose up --build`; `docker compose run --rm tests`), sem passos manuais.
- **SC-002**: **100%** das respostas de erro exercitadas pela suíte (404, 405, 422, 500 e 503) seguem o formato padronizado e validam contra o contrato.
- **SC-003**: `/health` responde em menos de **1 segundo** em ambiente local, com o banco disponível e com o banco indisponível.
- **SC-004**: Cobertura de linhas e ramificações do pacote `cofre` **≥ 85%** na suíte padrão.
- **SC-005**: **100%** dos cenários de aceitação e casos de borda desta spec têm ao menos um teste marcado, e todos os requisitos do escopo da unidade (RF-01, RNF-08 a RNF-11, RNF-13 a RNF-15) aparecem em `reports/rastreabilidade.md` com pelo menos um teste aprovado.
- **SC-006**: A suíte padrão termina em menos de **60 segundos** localmente e produz o mesmo resultado em **3 execuções consecutivas** e com ordem de testes aleatória.
- **SC-007**: **Zero** ocorrências de valores marcadores sensíveis nos logs capturados pelos testes de higiene de log.
- **SC-008**: Um PR com erro de lint ou teste falhando é sinalizado como falho pelo CI em **100%** dos casos; um PR correto passa nos três jobs.

## Assumptions

- A unidade não cria tabelas de domínio; a camada de persistência entrega conexão, sessão por requisição e inicialização do schema, que as unidades 002 e 003 preenchem.
- As rotas usadas nos testes de 422 e 500 existem **só na suíte de testes**, registradas na aplicação de teste; a aplicação de produção não expõe rotas de diagnóstico.
- As fixtures de domínio de docs/07 §3.2 (`make_user`, `auth_client`, `auth_client_factory`, `make_credential`, `raw_database`) chegam com as unidades 002 e 003, que criam as entidades correspondentes.
- O nível `perf` fica registrado e fora da execução padrão, mas não há testes de desempenho nesta unidade (RNF-12 é da unidade 003). O job manual de desempenho no CI entra junto com o primeiro teste `perf`.
- Os *status checks* do CI passam a ser exigidos na proteção de `main` e `develop` depois do merge do PR que criar o workflow (docs/06 §6).
- Os testes de fumaça controlam o Docker Compose da máquina, com projeto próprio (`cofre-smoke`) que é removido ao final, e acessam a API por `localhost:8000`, que precisa estar livre. Isso não conta como rede externa, e esses testes ficam fora da execução padrão.
- A verificação em Windows (RNF-15) segue a coluna *Verificação* de docs/02, "uso local em Windows": o mantenedor roda `uv sync` e `uv run pytest` na própria máquina e registra o resultado no relatório de execução. O CI roda em Linux.
- A aplicação não termina TLS e não aplica limites de tamanho de corpo nesta unidade (docs/04 §6).

## Histórico de revisões

| Versão | Data | Mudança | Motivo | Origem |
|--------|------|---------|--------|--------|
| 1.0.0 | 2026-09-13 | Versão aprovada | — | [PR #7](https://github.com/GuidaGaita/bootcamp/pull/7) |
