# 05 — Processo SDD (Specification-Driven Development)

> **Status:** Aprovado · **Versão:** 1.0.0 · **Última revisão:** 2026-09-13
> Ferramenta: **GitHub Spec Kit 1.0.6** integrado ao **Claude Code** ([ADR-0004](adr/0004-sdd-com-github-spec-kit.md)).

## 1. Princípio

**A especificação é a fonte da verdade; o código é consequência dela.** Nenhum comportamento entra no sistema sem estar descrito em uma spec aprovada, e nenhuma divergência entre spec e código é corrigida "só no código".

## 2. Hierarquia de artefatos

Em caso de conflito, **o artefato de nível mais alto prevalece** e o de nível mais baixo deve ser corrigido.

| Nível | Artefato | Responde |
|:-----:|----------|----------|
| 1 | [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) | Quais princípios são inegociáveis? |
| 2 | [`docs/`](README.md) — visão, requisitos, arquitetura, segurança, ADRs | O que é o produto e quais decisões valem para todo o projeto? |
| 3 | `specs/NNN-unidade/spec.md` | **O quê** e **por quê** desta unidade (histórias, cenários, FRs, casos de borda). |
| 4 | `specs/NNN-unidade/plan.md` + `research.md`, `data-model.md`, `contracts/`, `quickstart.md` | **Como** esta unidade será construída. |
| 5 | `specs/NNN-unidade/tasks.md` | Em quais passos executáveis e ordenados. |
| 6 | Testes → código | A prova e a implementação. |

## 3. Ciclo de vida de uma unidade

Cada unidade do [roadmap](09-roadmap.md) passa por **duas fases, cada uma com seu próprio PR**.

```mermaid
flowchart TD
  I["Issue da unidade<br/>(GitHub Projects)"] --> G{"Ideia madura?"}
  G -- "não" --> GM["/grill-me"] --> SA
  G -- "sim" --> SA
  subgraph A["Fase A · branch spec/NNN-slug"]
    SA["/speckit-specify"] --> CL["/speckit-clarify"]
    CL --> PL["/speckit-plan"]
    PL --> TK["/speckit-tasks"]
    TK --> AN["/speckit-analyze"]
    AN --> PRA["PR de spec → develop<br/>revisão e merge"]
  end
  PRA --> TI["/speckit-taskstoissues"]
  TI --> IMP
  subgraph B["Fase B · branch feature/NNN-slug"]
    IMP["/speckit-implement<br/>(testes primeiro)"] --> CV["/speckit-converge"]
    CV --> TS["Suíte completa + relatório"]
    TS --> PRB["PR de implementação → develop<br/>revisão e merge"]
  end
```

### Fase A — Especificação

1. Mover a issue da unidade para **Em andamento** e criar a branch `spec/NNN-slug` a partir de `develop`.
2. *(Opcional)* Rodar `/grill-me` se ainda houver decisões em aberto; registrar o resultado em [`docs/sessoes/`](sessoes/).
3. `/speckit-specify <descrição da unidade>` — gera `specs/NNN-slug/spec.md`. Cada `FR-xxx` deve citar os `RF-xx`/`RN-xx` de [02-requisitos.md](02-requisitos.md) que detalha.
4. `/speckit-clarify` — elimina todos os marcadores `[NEEDS CLARIFICATION]`.
5. `/speckit-plan <diretrizes técnicas>` — gera plano, pesquisa, modelo de dados, contratos e quickstart. O **Constitution Check** do plano precisa passar.
6. *(Opcional)* `/speckit-checklist` — checklist de qualidade dos requisitos.
7. `/speckit-tasks` — gera `tasks.md`, com testes antes da implementação.
8. `/speckit-analyze` — análise de consistência entre spec, plano e tarefas; achados **críticos** devem ser resolvidos.
9. Abrir o **PR de spec** para `develop`. No merge, a spec passa ao status **Aprovada** e a [matriz de rastreabilidade](02-requisitos.md#4-matriz-de-rastreabilidade) é atualizada.

### Fase B — Implementação

10. `/speckit-taskstoissues` — publica as tarefas como issues vinculadas ao milestone do incremento.
11. Criar a branch `feature/NNN-slug` a partir de `develop`.
12. `/speckit-implement` em **TDD**: testes de aceitação e de borda primeiro (vermelho) → implementação mínima (verde) → refatoração.
13. `/speckit-converge` — confirma que o código cobre spec, plano e tarefas; o que faltar vira nova tarefa.
14. Rodar a suíte completa, gerar o relatório de execução ([07-estrategia-de-testes.md](07-estrategia-de-testes.md#6-relatórios-e-evidências)) e abrir o **PR de implementação**. No merge, a spec passa a **Implementada**.

## 4. Status de uma spec

```mermaid
stateDiagram-v2
  [*] --> Rascunho
  Rascunho --> EmRevisao: PR de spec aberto
  EmRevisao --> Rascunho: mudanças solicitadas
  EmRevisao --> Aprovada: PR mergeado
  Aprovada --> Implementada: PR de implementação mergeado
  Implementada --> Revisada: refinamento registrado
  Revisada --> Implementada: código ajustado e mergeado
```

O campo `**Status**` do template do Spec Kit usa estes valores em pt-BR: `Rascunho`, `Em revisão`, `Aprovada`, `Implementada`, `Revisada`.

## 5. Refinamento por feedback

Specs evoluem. O que não pode acontecer é evoluírem **silenciosamente**.

**Gatilhos:** um teste revela ambiguidade ou contradição; a revisão de um PR aponta lacuna; a implementação mostra que algo é inviável; `/speckit-analyze` ou `/speckit-converge` encontram divergência; um bug expõe um caso não especificado.

**Procedimento:**

1. Abrir issue com o template **Mudança de especificação** (label `spec-change`).
2. Na branch de trabalho, alterar **primeiro o artefato de nível mais alto afetado** (docs → spec → plan → tasks).
3. Registrar a mudança na seção **Histórico de revisões** da spec e incrementar a versão:
   - **MAJOR** — contrato incompatível (endpoint, campo ou código de erro muda);
   - **MINOR** — novo requisito, cenário ou caso de borda;
   - **PATCH** — esclarecimento sem mudança de comportamento.
4. Adicionar uma linha em [registro-de-refinamentos.md](registro-de-refinamentos.md).
5. Criar ou ajustar o teste que reproduz o feedback; **só então** alterar o código.
6. Abrir o PR com a label `spec-change`, referenciando a issue.

Formato da seção, adicionada ao final de toda `spec.md`:

```markdown
## Histórico de revisões

| Versão | Data       | Mudança                                   | Motivo                                         | Origem          |
|--------|------------|-------------------------------------------|------------------------------------------------|-----------------|
| 1.0.0  | AAAA-MM-DD | Versão aprovada                           | —                                              | PR #N           |
| 1.1.0  | AAAA-MM-DD | Novo caso de borda: busca com termo vazio | Teste de borda revelou comportamento indefinido | Teste · PR #M   |
```

## 6. Rastreabilidade

```mermaid
flowchart LR
  RF["RF-xx / RN-xx<br/>docs/02-requisitos.md"] --> FR["FR-xxx<br/>spec.md"]
  FR --> T["T0xx<br/>tasks.md"]
  FR --> TE["teste com<br/>@pytest.mark.req('RF-xx')"]
  T --> C["código"]
  TE --> C
```

- Todo `FR-xxx` de uma spec cita ao menos um `RF-xx`, `RNF-xx` ou `RN-xx`.
- Todo teste de aceitação ou de borda recebe `@pytest.mark.req(...)` com os IDs que verifica.
- O harness gera `reports/rastreabilidade.md` (requisito → testes), usado para atualizar a matriz em [02-requisitos.md](02-requisitos.md#4-matriz-de-rastreabilidade).

## 7. Definições de Pronto e de Concluído

**Spec pronta para implementar (DoR):**

- [ ] Nenhum `[NEEDS CLARIFICATION]` restante.
- [ ] Cada história tem prioridade, teste independente e cenários *Given/When/Then*.
- [ ] Casos de borda listados, incluindo os do [catálogo](07-estrategia-de-testes.md#4-catálogo-inicial-de-casos-de-borda) aplicáveis.
- [ ] Todo `FR-xxx` rastreia para `RF`/`RNF`/`RN`.
- [ ] Plano passou no Constitution Check; contratos definidos em `contracts/`.
- [ ] `tasks.md` gerado; `/speckit-analyze` sem achados críticos.
- [ ] PR de spec revisado e mergeado.

**Unidade concluída (DoD):**

- [ ] Todos os cenários de aceitação e casos de borda automatizados e passando.
- [ ] Cobertura ≥ 85% e `ruff` sem erros; CI verde.
- [ ] Nenhuma divergência pendente entre spec e código (`/speckit-converge`).
- [ ] README, docs, ADRs e matriz de rastreabilidade atualizados.
- [ ] Relatório de execução publicado em [`docs/relatorios/`](relatorios/).
- [ ] PR de implementação revisado e mergeado.

## 8. Convenções de uso do Spec Kit neste repositório

| Convenção | Detalhe |
|-----------|---------|
| Numeração | Sequencial (`feature_numbering: sequential`). O `NNN` da spec **é o número da unidade** no roadmap; por isso, as specs são criadas na ordem das unidades. |
| Branches | A extensão `git` do Spec Kit **não** está instalada; as branches `spec/NNN-slug` e `feature/NNN-slug` são criadas manualmente, seguindo [06-governanca.md](06-governanca.md). |
| Idioma | Os títulos de seção dos templates permanecem em **inglês** (os comandos do Spec Kit dependem deles); todo o conteúdo é escrito em **pt-BR**. |
| Scripts | Variante **Python** (`.specify/scripts/python/`), portável entre Windows, Linux e CI. |
| Arquivos gerados | Não editar à mão `.specify/scripts/`, `.specify/templates/` nem `.claude/skills/speckit-*`. Atualizações seguem [08-ambiente-e-agentes.md](08-ambiente-e-agentes.md#55-atualização-das-ferramentas). |
