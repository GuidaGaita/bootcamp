# CLAUDE.md

Instruções do Claude Code para este repositório. Valem para toda sessão.

## Projeto

**Cofre**: API REST multiusuário de gerenciamento de senhas (Python 3.13, FastAPI, SQLite), desenvolvida com **Specification-Driven Development** usando o **GitHub Spec Kit**. Projeto individual de bootcamp, mantido por @GuidaGaita.

**Estado atual:** incremento 1 em andamento. A spec da unidade 001 ([specs/001-fundacao-da-api/](specs/001-fundacao-da-api/spec.md)) está aprovada, com plano, contrato e `tasks.md`; cada tarefa é publicada como issue `T0xx:` (labels `tipo:tarefa` e `unidade:001`, milestone "Incremento 1 — Fundação") logo após o merge da spec. **Ainda não existe código de aplicação.** O próximo passo é a Fase B, na branch `feature/001-fundacao-da-api` ([docs/09-roadmap.md](docs/09-roadmap.md)).

## Fontes da verdade (ordem de precedência)

1. [.specify/memory/constitution.md](.specify/memory/constitution.md): princípios inegociáveis.
2. [docs/](docs/README.md): [02-requisitos](docs/02-requisitos.md) (RF/RNF/RN), [03-arquitetura](docs/03-arquitetura.md), [04-seguranca](docs/04-seguranca.md) (normativo) e [adr/](docs/adr/README.md).
3. `specs/NNN-*/spec.md` → `plan.md` → `tasks.md`.
4. Testes → código.

Em conflito, o nível mais alto vence. Nunca resolva uma divergência alterando só o código.

## Regras inegociáveis

- **Sem spec aprovada, sem código.** Implemente apenas unidades cuja spec já foi mergeada em `develop` e que tenham `tasks.md`.
- **Spec primeiro.** Se um teste, uma revisão ou a implementação revelar lacuna ou contradição, pare. Atualize a spec (seção "Histórico de revisões" + [docs/registro-de-refinamentos.md](docs/registro-de-refinamentos.md)), depois o teste, depois o código, e avise o mantenedor.
- **Testes antes do código.** Todo cenário de aceitação e todo caso de borda vira teste com `@pytest.mark.req("RF-xx", ...)`.
- **Nunca commite em `main` ou `develop`.** Sempre branch de trabalho + PR ([docs/06-governanca.md](docs/06-governanca.md)).
- **Não invente requisitos.** O que não está especificado vira pergunta ao mantenedor ou `[NEEDS CLARIFICATION]` na spec.
- **Decisão arquitetural = ADR** em [docs/adr/](docs/adr/README.md) (use o template) + linha na tabela do [README.md](README.md), no mesmo PR.
- **Segurança** ([docs/04-seguranca.md §5](docs/04-seguranca.md#5-regras-obrigatórias-de-implementação)):
  - nunca use `random` para valores de segurança; use `secrets`;
  - nunca registre ou exponha senha, senha mestra, token, chaves, `ciphertext`, corpo de requisição ou cabeçalho `Authorization`;
  - toda consulta de sessão ou credencial filtra por `user_id`; recurso de outro usuário → 404;
  - use apenas `cryptography` e `argon2-cffi`, nunca criptografia própria;
  - mudar algoritmo, parâmetro mínimo ou fluxo de chaves exige ADR.

## Fluxo SDD ([docs/05-processo-sdd.md](docs/05-processo-sdd.md))

| Fase | Branch | Sequência |
|------|--------|-----------|
| A. Especificação | `spec/NNN-slug` | `/grill-me` (se houver decisões abertas) → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → PR |
| B. Implementação | `feature/NNN-slug` | `/speckit-taskstoissues` → `/speckit-implement` (TDD) → `/speckit-converge` → suíte + relatório → `/code-review` → PR |

Convenções do Spec Kit neste repositório:

- O `NNN` da spec é o número da unidade no roadmap; crie as specs em ordem numérica.
- Mantenha os títulos de seção dos templates em inglês e escreva o conteúdo em pt-BR.
- Todo `FR-xxx` cita os IDs de [docs/02-requisitos.md](docs/02-requisitos.md) que detalha.
- Toda `spec.md` termina com a seção `## Histórico de revisões`.
- Status da spec: `Rascunho` · `Em revisão` · `Aprovada` · `Implementada` · `Revisada`.
- A extensão git do Spec Kit não está instalada: crie as branches manualmente.
- Não edite à mão `.specify/scripts/`, `.specify/templates/*.md` nem `.claude/skills/speckit-*`. Personalizações de template vão em `.specify/templates/overrides/` (já existe um `spec-template.md`).
- `/speckit-taskstoissues` exige o servidor MCP do GitHub. Sem ele, crie as issues com `gh issue create`, uma por tarefa, com título `T0xx: <descrição>` e labels `tipo:tarefa` e `unidade:NNN`.

## Git e GitHub

- Branches `spec/`, `feature/`, `fix/`, `docs/` e `chore/` saem de `develop`; `hotfix/` sai de `main`. Slug em kebab-case, sem acentos.
- Commits em Conventional Commits com descrição em pt-BR (ex.: `feat(002): implementa login com bloqueio`) e rodapé `Co-Authored-By` do Claude.
- PR para `develop` com o template preenchido e `Closes #N`. Merge com **merge commit** (`gh pr merge --merge --delete-branch`), só depois da revisão tratada e do CI verde.
- Revisão em projeto individual: autorrevisão + `/code-review` (e `/security-review` quando tocar `crypto`/auth) com achados publicados no PR, e cada comentário respondido.
- Release: PR `develop → main` intitulado `release: vX.Y.Z`, seguido de tag.

## Código (a partir do incremento 1)

- Layout `src/cofre/` com as camadas `api → services → (crypto, repositories) → core` ([docs/03-arquitetura.md](docs/03-arquitetura.md)). Nenhuma camada importa uma camada acima; `services` não importa FastAPI.
- Identificadores, nomes de testes e docstrings em inglês. Mensagens de erro ao usuário em pt-BR, com `code` estável em inglês.
- Type hints em funções públicas; `ruff check` e `ruff format` limpos.
- Relógio e aleatoriedade são injetáveis. Testes nunca usam `sleep` nem rede.

## Comandos

Disponíveis a partir do incremento 1:

```bash
uv sync                                        # instala dependências
uv run pytest                                  # suíte completa com gate de cobertura
uv run pytest -m unit                          # subconjunto por marcador
uv run ruff check . && uv run ruff format --check .
docker compose up --build                      # API em http://localhost:8000/docs
docker compose run --rm tests                  # suíte em container, relatórios em ./reports
```

O ambiente local é Windows (PowerShell/Git Bash); os scripts do Spec Kit são Python (`.specify/scripts/python/`).

## Comunicação

- Responda e documente em pt-BR.
- Ao concluir uma tarefa, informe o que mudou, quais specs e requisitos foram afetados e o resultado real dos testes, inclusive falhas.
- Sessões com decisões relevantes são resumidas em [docs/sessoes/](docs/sessoes/).
