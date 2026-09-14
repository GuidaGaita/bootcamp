# Sessão grill-me — definição inicial do Cofre

| Campo | Valor |
|-------|-------|
| **Data** | 2026-09-13 |
| **Participantes** | @GuidaGaita (mantenedor) · Claude Code (Claude Opus 5) |
| **Skill** | `/grill-me` → `grilling`, de [mattpocock/skills](https://github.com/mattpocock/skills) @ `3cca18b` |
| **Objetivo** | Entender o sistema antes de escrever a documentação do projeto |
| **Resultado** | Documentação do incremento 0 (`docs/`, ADRs, `CLAUDE.md`, `README.md`, constituição) |

## 1. Pedido inicial

> Gerenciador de senhas simples, desenvolvido com SDD de forma incremental, em que documentação e especificações são a fonte da verdade. Tarefa: baixar a skill grill-me, conduzir a sessão e produzir **apenas a documentação** (sem specs e sem código).

## 2. Fatos levantados pelo agente, sem perguntar

- O repositório `GuidaGaita/bootcamp` é público e estava vazio (`main` sem commits), com Issues e Projects habilitados.
- O único colaborador era `GuidaGaita`.
- A máquina já tinha Node 22, Python 3.13, Docker 29 e `gh` autenticado. `uv` e `specify` não estavam instalados; o agente os instalou.
- A skill `grill-me` apenas delega à skill `grilling`; ambas foram instaladas em `.claude/skills/`.

## 3. Rodada 1 — perguntas, recomendações e respostas

| Q | Tema | Recomendação do agente | Resposta do mantenedor | Decisão final |
|---|------|------------------------|------------------------|---------------|
| 1 | Idioma | Docs em pt-BR; código e commits em inglês | "pt-BR" | Docs, specs e descrições de commit em pt-BR; identificadores de código em inglês ([ADR-0002](../adr/0002-idioma-da-documentacao-e-do-codigo.md)) |
| 2 | Nome | "Cofre" | "pode inventar" | **Cofre** |
| 3 | Equipe | Listar membros; papéis rotativos por issue | "só eu" | Projeto individual; revisão adaptada ([ADR-0012](../adr/0012-revisao-de-codigo-em-projeto-individual.md)) |
| 4 | Prazo e sprints | Sprints de 1 semana | "esquece isso" | Incrementos sem data ([09-roadmap.md](../09-roadmap.md)) |
| 5 | Formato do produto | API REST multiusuário, sem frontend | "não sei, decide" | Recomendação adotada ([ADR-0005](../adr/0005-api-rest-multiusuario-sem-frontend.md)) |
| 6 | Linguagem | Python + FastAPI + pytest | "Python" | [ADR-0006](../adr/0006-python-fastapi-uv.md) |
| 7 | Agentes de IA | `AGENTS.md` canônico + `CLAUDE.md` | "só Claude Code, só `CLAUDE.md`" | [ADR-0003](../adr/0003-claude-code-como-agente-unico.md) |
| 8 | Estrutura SDD | Estrutura própria inspirada no Spec Kit | "GitHub Spec Kit" | [ADR-0004](../adr/0004-sdd-com-github-spec-kit.md) |
| 9 | Convenções Git | `main`/`develop`/`feature/*`, Conventional Commits, merge commit | "isso" | [ADR-0011](../adr/0011-fluxo-git.md) |
| 10 | Commit inicial | Commit mínimo em `main`, criar `develop`, PR de documentação | "pode ser" | Executado |

## 4. Delegação

Ao responder a rodada 1, o mantenedor **delegou ao agente as decisões restantes** e autorizou commits, push e merges. A sessão não seguiu para novas rodadas. O agente resolveu o restante da árvore de decisões e registrou cada escolha para revisão posterior:

| Decisão tomada pelo agente | Registro |
|----------------------------|----------|
| Escopo do MVP, prioridades MoSCoW e itens fora do escopo | [01-visao-geral.md](../01-visao-geral.md), [02-requisitos.md](../02-requisitos.md) |
| Regras de negócio: limites de campos, 1.000 credenciais, sessão de 30 min, bloqueio após 5 falhas | [02-requisitos.md](../02-requisitos.md#3-regras-de-negócio) |
| Persistência em SQLite | [ADR-0007](../adr/0007-sqlite-com-sqlalchemy.md) |
| Criptografia em envelope com Argon2id e AES-256-GCM | [ADR-0008](../adr/0008-criptografia-em-envelope.md) |
| Sessões com token opaco em vez de JWT | [ADR-0009](../adr/0009-sessoes-com-token-opaco.md) |
| Cifrar todos os campos da credencial | [ADR-0010](../adr/0010-cifrar-todos-os-campos-da-credencial.md) |
| Spec Kit com scripts Python e sem extensão git; duas fases e dois PRs por unidade | [ADR-0004](../adr/0004-sdd-com-github-spec-kit.md), [05-processo-sdd.md](../05-processo-sdd.md) |
| Harness com pytest e marcador de rastreabilidade | [ADR-0013](../adr/0013-harness-de-testes-com-pytest.md) |
| Docker Compose e GitHub Actions | [ADR-0014](../adr/0014-ambiente-reprodutivel-com-docker.md) |

## 5. Pontos para o mantenedor confirmar

Decisões tomadas por delegação que merecem um olhar humano antes da spec da unidade correspondente:

1. **Enumeração no cadastro:** o cadastro responde 409 para e-mail já existente (risco aceito em [04-seguranca.md](../04-seguranca.md#6-riscos-aceitos)).
2. **Endpoints públicos** para gerar e avaliar senhas, sem autenticação.
3. **Tempos:** sessão de 30 min com expiração absoluta; bloqueio de 15 min após 5 falhas.
4. **Proteção de branches:** adiada para o incremento 1, quando o CI existir.
