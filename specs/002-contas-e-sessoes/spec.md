# Feature Specification: Contas e sessões

**Feature Branch**: `spec/002-003-contas-e-cofre`

**Created**: 2026-09-30

**Status**: Implementada

**Versão**: 1.0.1

**Input**: User description: "Unidade 002 — Contas e sessões. Escopo: RF-02 a RF-07; RN-01 a RN-05, RN-12, RN-14, RN-16; RNF-02, RNF-04 a RNF-07. Cadastro, login com bloqueio, sessão com token opaco, logout, consulta de conta, troca de senha mestra e exclusão de conta."

> **Fontes normativas.** Esta spec não repete o que já está fixado em [docs/02](../../docs/02-requisitos.md) (RF/RN), [docs/03](../../docs/03-arquitetura.md) (modelo de dados, endpoints, erros), [docs/04](../../docs/04-seguranca.md) (algoritmos, AAD, ciclo de vida das chaves) e [docs/07](../../docs/07-estrategia-de-testes.md) §4 (casos de borda). Ela as **referencia** e fixa o contrato em [contracts/api.md](contracts/api.md). Em conflito, vale o documento de nível mais alto.

## Clarifications

### Session 2026-09-30

- Confirmados pelo mantenedor: `409 EMAIL_ALREADY_REGISTERED` no cadastro, sessão de 30 min com expiração absoluta e bloqueio de 15 min após 5 falhas (riscos aceitos em docs/04 §6).
- Token ausente ou malformado → **401 `UNAUTHENTICATED`** pelo formato padrão. A dependência lê o cabeçalho `Authorization` diretamente, sem `HTTPBearer`, que responderia com o formato do FastAPI (achado R3 do PR #63).
- `master_password` no login só precisa ter de 1 a 1024 caracteres: as regras de tamanho de RN-02 valem no cadastro e na troca, para o login não distinguir "senha curta" de "senha errada".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastro de conta (Priority: P1)

Um visitante cria uma conta com e-mail e senha mestra.

**Independent Test**: `uv run pytest tests/api/test_accounts.py -k register`

1. **Given** e-mail e senha válidos, **When** `POST /api/v1/accounts`, **Then** 201 com `id`, `email` normalizado e `created_at`; a senha não é devolvida nem armazenada (RNF-02).
2. **Given** um e-mail já cadastrado (inclusive com outra caixa ou espaços), **When** cadastra, **Then** 409 `EMAIL_ALREADY_REGISTERED`.
3. **Given** e-mail ou senha fora de RN-01/RN-02, **When** cadastra, **Then** 422 `VALIDATION_ERROR` com `details`.

### User Story 2 - Login, sessão e logout (Priority: P1)

O usuário autentica-se, usa o token e encerra a sessão.

**Independent Test**: `uv run pytest tests/api/test_sessions.py`

1. **Given** credenciais corretas, **When** `POST /api/v1/sessions`, **Then** 201 com `token` e `expires_at` 30 min depois (relógio controlado).
2. **Given** senha errada ou e-mail inexistente, **When** faz login, **Then** a resposta é 401 `INVALID_CREDENTIALS`, idêntica nos dois casos (RN-04).
3. **Given** 5 falhas seguidas, **When** tenta de novo, **Then** 429 com `Retry-After`, igual para e-mail cadastrado ou não; depois de 15 min o login volta (RN-14).
4. **Given** um token válido, **When** `DELETE /api/v1/sessions/current`, **Then** 204 e o token passa a receber 401.
5. **Given** token ausente, malformado, expirado ou revogado, **When** chama rota autenticada, **Then** 401 `UNAUTHENTICATED`.

### User Story 3 - Gestão da conta (Priority: P2)

O usuário consulta a conta, troca a senha mestra ou exclui a conta.

**Independent Test**: `uv run pytest tests/api/test_account_management.py`

1. **Given** sessão válida, **When** `GET /api/v1/accounts/me`, **Then** 200 com `id`, `email` e `created_at` (RF-05).
2. **Given** a senha atual correta, **When** `PUT /api/v1/accounts/me/master-password`, **Then** 204; todas as sessões caem; o login com a senha antiga falha e com a nova funciona; a DEK é a mesma (RF-06).
3. **Given** a senha atual errada em RF-06/RF-07, **Then** 403 `INVALID_MASTER_PASSWORD` e a sessão segue válida; a falha que atinge o limite revoga todas as sessões e bloqueia o e-mail; com o e-mail já bloqueado, 429 sem verificar a senha (RN-16).
4. **Given** a senha correta, **When** `POST /api/v1/accounts/me/deletion`, **Then** 204 e usuário, sessões e credenciais somem (RN-12).

## Edge Cases

Todos os casos da unidade 002 em [docs/07 §4](../../docs/07-estrategia-de-testes.md) são obrigatórios e viram testes `req`, inclusive:

- e-mail de 254 e 255 caracteres e sem `@`; senha de 11, 12, 128 e 129 caracteres; senha com e-mail dentro; acentos e emoji (RN-01, RN-02);
- `é` pré-composto no cadastro e `e` + acento combinante no login (NFKC);
- e-mail inexistente vs. senha errada; bloqueio idêntico para e-mail inexistente; falhas intercaladas com sucesso zeram o contador (RN-04, RN-14);
- token ausente, malformado (não é base64url ou não tem 32 bytes), expirado aos 31 min, após logout e após troca de senha (RN-05);
- troca de senha: credenciais continuam legíveis; senha atual errada → 403; 5ª falha → sessões revogadas; e-mail já bloqueado → 429 (RN-16).

Casos transversais de docs/07 aplicáveis à unidade: nenhum segredo (senha, token) em logs, erros ou `repr` (RNF-04); e-mails e senhas não aparecem nas respostas de erro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `POST /api/v1/accounts` DEVE cadastrar a conta e responder 201, com e-mail normalizado (strip + minúsculas) e único; duplicado → 409 `EMAIL_ALREADY_REGISTERED` (RF-02, RN-01).
- **FR-002**: O cadastro e a troca de senha DEVEM normalizar a senha em NFKC e validar RN-02 (12–128 caracteres, sem conter o e-mail sem diferenciar caixa); violação → 422 `VALIDATION_ERROR` com `details`, sem repetir o valor (RF-02, RF-06, RN-02).
- **FR-003**: O cadastro DEVE guardar apenas o hash Argon2id da senha, um `kdf_salt` independente, os parâmetros do KDF e a DEK aleatória embrulhada (AES-256-GCM, AAD `cofre:dek:v1:{user_id}`) pela KEK derivada, conforme docs/04 §3 e §4 (RNF-02, RNF-05).
- **FR-004**: `POST /api/v1/sessions` DEVE verificar a senha, devolver `token` (32 bytes aleatórios em base64url sem padding) e `expires_at`, e guardar só `SHA-256(token)` e a DEK embrulhada pela chave de sessão (HKDF-SHA256, AAD `cofre:session-dek:v1:{session_id}`); a expiração é absoluta, `COFRE_SESSION_TTL_MINUTES` (padrão 30); sessões expiradas do usuário são removidas no login (RF-03, RN-05, RNF-06).
- **FR-005**: A falha de login DEVE responder 401 `INVALID_CREDENTIALS` com a mesma mensagem para senha errada e e-mail inexistente; para e-mail inexistente, DEVE verificar a senha contra um hash fictício com os mesmos parâmetros (RN-04, docs/04 A3).
- **FR-006**: O login DEVE ser bloqueado após `COFRE_LOGIN_MAX_ATTEMPTS` (5) falhas seguidas por `COFRE_LOGIN_LOCK_MINUTES` (15) para um mesmo e-mail normalizado, cadastrado ou não, com 429 `TOO_MANY_ATTEMPTS` e `Retry-After` em segundos; o bloqueio é consultado **antes** de verificar a senha; o sucesso zera o contador; o controle usa `SHA-256(e-mail normalizado)` como chave. A tentativa é **contada antes** de verificar a senha, com uma operação atômica, para que tentativas paralelas não ultrapassem o limite; linhas sem atividade há mais de 24 h e sem bloqueio ativo são descartadas (RN-14, RNF-07).
- **FR-007**: Rotas autenticadas DEVEM ler `Authorization: Bearer <token>` e responder 401 `UNAUTHENTICATED` se o cabeçalho faltar, o token não decodificar em exatamente 32 bytes, a sessão não existir ou estiver expirada, com o cabeçalho `WWW-Authenticate: Bearer`; a DEK só existe em memória durante a requisição (RN-05, RNF-06).
- **FR-008**: `DELETE /api/v1/sessions/current` DEVE apagar a sessão e responder 204 (RF-04).
- **FR-009**: `GET /api/v1/accounts/me` DEVE responder 200 com `id`, `email` e `created_at` (RF-05).
- **FR-010**: `PUT /api/v1/accounts/me/master-password` DEVE, com a senha atual correta, gerar novo hash e novo `kdf_salt`, re-embrulhar a **mesma** DEK, zerar o contador do e-mail, remover **todas** as sessões e responder 204 (RF-06, RN-05).
- **FR-011**: Senha atual incorreta em RF-06/RF-07 DEVE responder 403 `INVALID_MASTER_PASSWORD` e contar no controle de FR-006; a falha que atinge o limite DEVE também bloquear o e-mail e revogar todas as sessões do usuário; com o e-mail já bloqueado DEVE responder 429 sem verificar a senha (RN-16, docs/04 A11).
- **FR-012**: `POST /api/v1/accounts/me/deletion` DEVE, com a senha correta, remover usuário, sessões e credenciais e responder 204 (RF-07, RN-12).
- **FR-013**: Senhas e tokens NUNCA DEVEM aparecer em logs, respostas de erro ou `repr` (campos `SecretStr`); segredos são comparados com `hmac.compare_digest`; toda aleatoriedade vem de `secrets`/`os.urandom`; só `cryptography` e `argon2-cffi` são usadas (RNF-04, RNF-05, docs/04 §5).
- **FR-014**: O catálogo de erros DEVE ganhar `UNAUTHENTICATED` (401), `INVALID_CREDENTIALS` (401), `INVALID_MASTER_PASSWORD` (403), `EMAIL_ALREADY_REGISTERED` (409) e `TOO_MANY_ATTEMPTS` (429), com mensagem em pt-BR (RNF-14).
- **FR-015**: O harness DEVE oferecer as fixtures `make_user`, `auth_client` e `auth_client_factory` (RNF-09).

### Key Entities

- **User** (`users`), **Session** (`sessions`) e **LoginThrottle** (`login_throttles`), conforme docs/03 §3. Sem chave estrangeira em `login_throttles`.

## Success Criteria *(mandatory)*

- **SC-001**: Cadastro → login → `/me` → logout funciona ponta a ponta com relógio controlado.
- **SC-002**: 100% dos casos de borda acima têm teste marcado com `req`; RF-02 a RF-07 e RN-01 a RN-05, RN-12, RN-14 e RN-16 aparecem em `reports/rastreabilidade.md`.
- **SC-003**: Suíte verde, cobertura ≥ 85%, `ruff` limpo e CI verde.
- **SC-004**: Login e cadastro < 1 s com os parâmetros mínimos do Argon2id (RNF-12).

## Assumptions

- Não há recuperação de senha mestra (RN-03). A sessão não é renovada.
- O desempenho (RNF-12) é verificado na unidade 003, com o marcador `perf`.
- Esta spec foi escrita sem `/speckit-clarify` e `/speckit-analyze`, por economia: as decisões abertas já estavam fechadas nos docs e na sessão acima.

## Histórico de revisões

| Versão | Data | Mudança | Motivo | Origem |
|--------|------|---------|--------|--------|
| 1.0.0 | 2026-09-30 | Versão aprovada | — | PR de spec das unidades 002 e 003 |
| 1.0.0 | 2026-10-01 | Status alterado para Implementada; conteúdo sem mudança | Fase B concluída | PR de implementação da unidade 002 |
| 1.0.1 | 2026-10-01 | FR-006: tentativa contada antes da verificação e limpeza de linhas ociosas (24 h); FR-007: 401 inclui `WWW-Authenticate: Bearer`; campos de senha e e-mail com limites estruturais (1024 e 320) | A contagem depois da verificação não era atômica e deixava passar tentativas paralelas; linhas de e-mails inexistentes cresciam sem limite | Revisão assistida por IA do PR #69 (R-026) |
