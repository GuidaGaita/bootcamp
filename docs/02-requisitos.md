# 02 — Requisitos e Regras de Negócio

> **Status:** Aprovado · **Versão:** 1.1.0 · **Última revisão:** 2026-09-13
> Catálogo de nível de projeto. Cada spec do Spec Kit (`specs/NNN-*/spec.md`) detalha os requisitos da sua unidade em `FR-xxx`, sempre referenciando os IDs deste documento.

## Convenções

- **IDs estáveis:** `RF-xx` (funcional), `RNF-xx` (não funcional), `RN-xx` (regra de negócio). Um ID nunca é reaproveitado; requisitos removidos ficam marcados como ~~riscados~~ com o motivo.
- **Prioridade (MoSCoW):** **Must** (obrigatório no MVP) · **Should** (importante, entra se possível) · **Could** (desejável) · **Won't** (fora do escopo, ver [01-visao-geral.md](01-visao-geral.md#52-fora-do-escopo)).
- **Unidade:** a unidade de especificação (spec do Spec Kit) responsável pelo requisito — ver [09-roadmap.md](09-roadmap.md#2-decomposição-em-unidades).
- Contratos detalhados (schemas de entrada/saída) ficam em `specs/NNN-*/contracts/`. A visão geral dos endpoints está em [03-arquitetura.md](03-arquitetura.md#6-visão-geral-da-api).

---

## 1. Requisitos funcionais

### Unidade 001 — Fundação da API

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-01 | O sistema deve expor um endpoint público de verificação de saúde que responda **200** quando a aplicação e o banco de dados estão operacionais e **503** quando o banco está indisponível, sem expor detalhes internos. | Must |

### Unidade 002 — Contas e sessões

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-02 | O visitante deve poder **cadastrar uma conta** informando e-mail e senha mestra. | Must |
| RF-03 | O usuário deve poder **autenticar-se** com e-mail e senha mestra, recebendo um token de sessão com data de expiração. | Must |
| RF-04 | O usuário autenticado deve poder **encerrar a sessão atual** (logout), invalidando o token imediatamente. | Must |
| RF-05 | O usuário autenticado deve poder **consultar os dados da própria conta** (id, e-mail, data de criação). | Should |
| RF-06 | O usuário autenticado deve poder **alterar a senha mestra**, informando a atual, sem perder nenhuma credencial. | Should |
| RF-07 | O usuário autenticado deve poder **excluir a própria conta**, confirmando com a senha mestra. | Could |

### Unidade 003 — Cofre de credenciais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-08 | O usuário autenticado deve poder **criar uma credencial** com título, senha e, opcionalmente, usuário, URL e notas. | Must |
| RF-09 | O usuário autenticado deve poder **listar suas credenciais** de forma paginada e ordenada por título, **sem** exibir as senhas. | Must |
| RF-10 | O usuário autenticado deve poder **buscar credenciais** por um termo que case com título, usuário ou URL. | Should |
| RF-11 | O usuário autenticado deve poder **consultar uma credencial** específica, incluindo a senha decifrada. | Must |
| RF-12 | O usuário autenticado deve poder **atualizar parcialmente** uma credencial. | Must |
| RF-13 | O usuário autenticado deve poder **excluir** uma credencial. | Must |

### Unidade 004 — Gerador e avaliador de senhas

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-14 | O sistema deve **gerar senhas aleatórias** conforme parâmetros de comprimento e conjuntos de caracteres. | Must |
| RF-15 | O sistema deve **avaliar a força** de uma senha, retornando pontuação, estimativa de tempo de quebra e sugestões. | Should |

### Unidade 005 — Saúde do cofre

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-16 | O usuário autenticado deve poder obter um **relatório de saúde** do cofre, listando credenciais com senha fraca e grupos de credenciais com senha reutilizada. | Could |

---

## 2. Requisitos não funcionais

| ID | Categoria | Requisito | Prioridade | Verificação |
|----|-----------|-----------|------------|-------------|
| RNF-01 | Segurança | Todos os campos de uma credencial devem ser armazenados **cifrados** com AES-256-GCM; nenhum dado de credencial em texto claro no banco. | Must | Teste de segurança inspeciona o SQLite. |
| RNF-02 | Segurança | A senha mestra **nunca** é armazenada; guarda-se apenas hash **Argon2id** com parâmetros mínimos OWASP (m=19 MiB, t=2, p=1). | Must | Teste unitário + revisão. |
| RNF-03 | Segurança | Um usuário **não pode** ler, alterar ou excluir recursos de outro; tentativas retornam **404** (não revelam existência). | Must | Testes de API (IDOR). |
| RNF-04 | Segurança | Senhas, senha mestra, tokens e chaves **nunca** aparecem em logs, mensagens de erro ou respostas, exceto a senha na consulta individual de credencial (RF-11) e a senha gerada (RF-14). | Must | Teste que captura logs + revisão. |
| RNF-05 | Segurança | Tokens, sais, nonces, chaves e senhas geradas usam **exclusivamente** fonte criptograficamente segura (`secrets` / `os.urandom`). | Must | Revisão + regra de lint. |
| RNF-06 | Segurança | Sessões usam **token opaco** com ≥ 256 bits de entropia, armazenado no servidor apenas como hash, com expiração configurável (padrão 30 min). | Must | Testes de sessão com relógio controlado. |
| RNF-07 | Segurança | O login e as operações autenticadas que exigem a senha mestra devem ser protegidos contra força bruta conforme RN-14 e RN-16. | Should | Testes de API. |
| RNF-08 | Interoperabilidade | A API deve ser JSON, versionada em `/api/v1`, publicar especificação **OpenAPI 3** (`/openapi.json`, `/docs`) e usar o formato de erro padronizado. | Must | Testes de contrato. |
| RNF-09 | Testabilidade | Cobertura de **linhas e ramificações** (*branch coverage*) ≥ **85%** no pacote `cofre`; todo requisito *Must* com ao menos um teste marcado com seu ID. | Must | Gate de cobertura + relatório de rastreabilidade. |
| RNF-10 | Reprodutibilidade | O ambiente deve subir com `docker compose up` e os testes rodar com um único comando; dependências travadas em `uv.lock`. | Must | Execução em máquina limpa / CI. |
| RNF-11 | Qualidade | Código sem erros de `ruff` (lint e formatação) e com *type hints* em funções públicas; o CI bloqueia PRs que falharem. | Must | GitHub Actions. |
| RNF-12 | Desempenho | Operações de cofre (RF-08 a RF-13 e RF-16) com p95 < **200 ms** para cofres de até 1.000 credenciais de tamanho típico (até 1 KB de texto claro cada) em ambiente local; operações com Argon2id (RF-02, RF-03, RF-06, RF-07) < **1 s**. | Should | Testes de desempenho (marcador `perf`). |
| RNF-13 | Observabilidade | Logs estruturados (JSON) por requisição com id, método, rota, status e duração, sem dados sensíveis. | Could | Teste que valida o formato do log. |
| RNF-14 | Usabilidade da API | Erros com `code` estável em inglês (ex.: `INVALID_CREDENTIALS`) e `message` legível em pt-BR. | Should | Testes de contrato. |
| RNF-15 | Portabilidade | Executar em Python 3.13 em Linux (container) e em Windows/macOS via `uv`. | Should | CI em Linux + uso local em Windows. |

---

## 3. Regras de negócio

| ID | Regra | Relacionado |
|----|-------|-------------|
| RN-01 | O **e-mail** identifica a conta de forma única. Deve ter formato válido e no máximo **254 caracteres**. É normalizado (espaços nas pontas removidos, minúsculas) antes de validar unicidade e autenticar. | RF-02, RF-03 |
| RN-02 | A **senha mestra** é normalizada em Unicode **NFKC** antes de qualquer validação, hash ou derivação de chave. Após a normalização, deve ter entre **12 e 128 caracteres** e **não pode conter o e-mail** do usuário (comparação sem diferenciar maiúsculas de minúsculas). Não há regras de composição obrigatória (alinhado ao NIST SP 800-63B). | RF-02, RF-03, RF-06 |
| RN-03 | **Não existe recuperação de senha mestra.** Se ela for esquecida, os dados do cofre são irrecuperáveis. | RF-02 |
| RN-04 | Falhas de autenticação retornam **mensagem genérica**, sem indicar se o e-mail existe ou se a senha está errada. | RF-03 |
| RN-05 | Uma sessão expira **30 minutos** após o login (expiração absoluta, configurável). O logout invalida a sessão atual; a alteração da senha mestra invalida **todas** as sessões do usuário, inclusive a atual. | RF-03, RF-04, RF-06 |
| RN-06 | Campos da credencial: `title` obrigatório (1–100 caracteres, não vazio após remover espaços); `password` obrigatório (1–1024); `username` opcional (≤ 255); `url` opcional (≤ 2048, esquema `http` ou `https`); `notes` opcional (≤ 10.000). Títulos duplicados são permitidos. | RF-08, RF-12 |
| RN-07 | Cada usuário pode ter no máximo **1.000 credenciais**. | RF-08 |
| RN-08 | A **listagem, a busca e o relatório de saúde nunca retornam senhas**; a senha só aparece na consulta individual. | RF-09, RF-10, RF-11, RF-16 |
| RN-09 | Uma credencial pertence **exclusivamente** ao usuário que a criou; não há compartilhamento. | RF-08..RF-13 |
| RN-10 | **Gerador:** comprimento de 8 a 128 (padrão 20); conjuntos `lowercase`, `uppercase`, `digits`, `symbols` (padrão: todos); ao menos um conjunto selecionado; a senha contém **ao menos um caractere de cada conjunto selecionado**; opção `exclude_ambiguous` remove `0 O o 1 l I \|`. Como o comprimento mínimo (8) supera o número de conjuntos (4), sempre é possível incluir um caractere de cada conjunto. | RF-14 |
| RN-11 | **Força de senha:** a entrada do avaliador deve ter de 1 a 1024 caracteres (mesmo limite de `password` em RN-06). A pontuação vai de 0 (muito fraca) a 4 (muito forte); uma senha é considerada **fraca** quando a pontuação é ≤ 2. | RF-15, RF-16 |
| RN-12 | A **exclusão de conta** é definitiva e remove todas as credenciais e sessões do usuário. | RF-07 |
| RN-13 | **Paginação:** `limit` entre 1 e 100 (padrão 20) e `offset` ≥ 0; um `offset` além do total retorna lista vazia (não é erro). | RF-09, RF-10 |
| RN-14 | Após **5 falhas consecutivas** de login para um mesmo e-mail normalizado, **cadastrado ou não**, novas tentativas são bloqueadas por **15 minutos** (HTTP 429). O comportamento é idêntico para e-mails inexistentes, para não revelar quais contas existem (RN-04). Um login bem-sucedido zera o contador. | RF-03, RN-04, RNF-07 |
| RN-15 | A busca é **case-insensitive** por substring nos campos título, usuário e URL. | RF-10 |
| RN-16 | Falhas na verificação da senha mestra em operações autenticadas (RF-06, RF-07) respondem **403** e contam no mesmo controle de tentativas de RN-14, pelo e-mail do usuário. A falha que **atinge o limite** também responde 403, bloqueia o e-mail por 15 minutos e **revoga todas as sessões do usuário**: a partir daí o token recebe 401 e o login recebe 429 até o fim do bloqueio. Se o e-mail já estiver bloqueado (por exemplo, por falhas de login enquanto há uma sessão ativa em outro dispositivo), RF-06 e RF-07 respondem **429** sem verificar a senha. Assim, um token roubado não serve para adivinhar a senha mestra. | RF-06, RF-07, RN-14, RNF-07 |

---

## 4. Matriz de rastreabilidade

Atualizada a cada spec aprovada e a cada unidade implementada.

| Requisito | Unidade | Spec | Testes | Status |
|-----------|---------|------|--------|--------|
| RF-01 | 001 | — | — | Planejado |
| RF-02 .. RF-07 | 002 | — | — | Planejado |
| RF-08 .. RF-13 | 003 | — | — | Planejado |
| RF-14, RF-15 | 004 | — | — | Planejado |
| RF-16 | 005 | — | — | Planejado |
| RNF-01 .. RNF-15 | conforme [09-roadmap.md](09-roadmap.md#2-decomposição-em-unidades) | — | — | Planejado |
| RN-01 .. RN-16 | conforme [09-roadmap.md](09-roadmap.md#2-decomposição-em-unidades) | — | — | Planejado |

**Legenda de status:** Planejado → Especificado (spec aprovada) → Implementado (testes verdes) → Revisado (houve refinamento registrado).

---

## 5. Histórico de revisões

| Versão | Data | Mudança | Origem |
|--------|------|---------|--------|
| 1.0.0 | 2026-09-13 | Versão inicial; RN-14 passa a valer para qualquer e-mail (R-007). | PR #1 |
| 1.1.0 | 2026-09-13 | Nova RN-16 (força bruta da senha mestra com token); RN-01 com formato e tamanho; RN-02 com normalização NFKC; RN-08 inclui o relatório de saúde; RN-10 sem cláusula inalcançável; RN-11 com limite de entrada; RF-01 com 200/503; RNF-07, RNF-09 e RNF-12 ajustados; RN-16 esclarecida na revisão do PR #3. | Auditoria da documentação (R-008, R-009, R-012 a R-014, R-016, R-019) |
