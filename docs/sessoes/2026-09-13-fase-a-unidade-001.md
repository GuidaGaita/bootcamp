# Sessão — Fase A da unidade 001 (Fundação da API)

| Campo | Valor |
|-------|-------|
| **Data** | 2026-09-13 |
| **Participantes** | @GuidaGaita (mantenedor, por delegação) · Claude Code (Claude Opus 5) |
| **Skills** | `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` |
| **Objetivo** | Preparar o GitHub para o incremento 1 e especificar a unidade 001 sem gerar código |
| **Resultado** | Milestones, proteção de branches, issue da unidade, `specs/001-fundacao-da-api/` completo e ADRs 0015 e 0016 |

## 1. GitHub

- Milestones "Incremento 1 — Fundação" a "Incremento 5 — Saúde do cofre e fechamento" criados.
- Issue [#5 — Unidade 001](https://github.com/GuidaGaita/bootcamp/issues/5) com as labels `tipo:unidade`, `unidade:001` e `prioridade:must`.
- Proteção de `main` e `develop`: PR com 0 aprovações, resolução de conversas, bloqueio de *force push* e exclusão, `enforce_admins`. Registrada em docs/06 pelo [PR #6](https://github.com/GuidaGaita/bootcamp/pull/6), cuja revisão teve 2 achados corrigidos.
- Board "Cofre" **pendente**: o token do `gh` não tem o escopo `project`. O mantenedor precisa rodar `gh auth refresh -s project`.

## 2. Clarificações respondidas pela documentação

Nenhuma exigiu decisão de produto do mantenedor.

| Pergunta | Resposta | Fonte |
|----------|----------|-------|
| Código para método HTTP não suportado | 405 `METHOD_NOT_ALLOWED`, acrescentado a docs/03 | RNF-08 (R-022) |
| Letras Unicode no `X-Request-ID` | Não; apenas ASCII | docs/03 §6.2 (anti-injeção em log) |
| Caminho bruto no log | Não; modelo de rota ou nulo, sem *query string* | RNF-04, docs/04 §5 |
| Alcance do `Cache-Control: no-store` | Toda resposta sob `/api/v1`, inclusive erros | docs/03 §6.2, ameaça A9 |
| Iniciar com banco indisponível | Sim; `/health` responde 503 e se recupera sozinho | RF-01 |

## 3. Decisões técnicas

| Decisão | Registro |
|---------|----------|
| Borda HTTP num único middleware ASGI (request ID, cabeçalhos, log JSON, 500 padronizado) e Uvicorn sem log de acesso | [ADR-0015](../adr/0015-borda-http-com-middleware-asgi-unico.md) |
| Testes de API validados contra `contracts/openapi.yaml` com `jsonschema` | [ADR-0016](../adr/0016-testes-de-contrato-contra-openapi-da-spec.md) |
| Imagem instala o lock com `--frozen` (ADR-0014); lock desatualizado é detectado no CI | research R15–R16 |
| Gate de cobertura só na seleção padrão; subconjuntos geram relatórios sem gate | research R14 |
| Testes de fumaça controlam o compose em projeto isolado `cofre-smoke`; teste automatizado da estrutura do CI | research R21 |

## 4. Achados do `/speckit-analyze`

| ID | Severidade | Achado | Tratamento |
|----|------------|--------|------------|
| C1 | CRITICAL | Cenários da US4 (Docker, volume, CI, Windows) verificados só manualmente, contra o princípio III | Testes `smoke` com compose e teste do workflow; Windows segue a verificação de RNF-15 em docs/02 |
| I1 | MEDIUM | SC-005 tratava RNF-13 a RNF-15 como *Must* | Critério reescrito |
| I2 | MEDIUM | "PR não mergeável" antes de existirem *status checks* obrigatórios | Cenário reescrito |
| I3 | LOW | Árvore do plano sem alguns arquivos de teste | Árvore atualizada |
| U1, U2 | LOW | SC-003 medido manualmente; testes de `pytester` antes do plugin dão erro, não falha | Aceitos |

## 5. Pendências

- Board "Cofre" no GitHub Projects, depois de `gh auth refresh -s project`; em seguida, incluir nele a issue #5 e as issues de tarefa.
- Antes da spec 002, confirmar os riscos aceitos na sessão grill-me: 409 no cadastro, endpoints públicos do gerador e do avaliador, e sessão de 30 min com bloqueio de 15 min.
