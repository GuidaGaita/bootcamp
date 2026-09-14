# ADR-0011 — Fluxo Git com `main`, `develop` e branches de trabalho

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita (base do fluxo); Claude Code (prefixo `spec/`, por delegação)
- **Relacionados:** [06-governanca.md](../06-governanca.md), [Sessão grill-me Q9](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [R-006](../registro-de-refinamentos.md)

## Contexto

A entrega exige um fluxo de versionamento estruturado (ex.: `main`, `develop`, `feature/*`) e proíbe commits diretos na branch principal. O processo SDD tem duas fases por unidade, especificação e implementação, que devem ser revisadas separadamente.

## Decisão

- **Branches permanentes:** `main` (versões liberadas, com tags SemVer) e `develop` (integração).
- **Branches de trabalho:** `spec/NNN-slug` (Fase A), `feature/NNN-slug` (Fase B), `fix/`, `docs/`, `chore/`, todas saindo de `develop`; e `hotfix/`, saindo de `main`.
- **Nenhum commit direto** em `main` ou `develop`. A única exceção foi o commit inicial, necessário para criar as branches.
- **Conventional Commits**, com descrição em pt-BR.
- **Merge commit** em todos os PRs (sem *squash*), preservando o histórico de commits e da revisão.
- **Release** por PR `develop → main`, seguido de tag `vX.Y.Z`.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| GitHub Flow (somente `main` + branches) | Não atende à estrutura `main`/`develop` pedida na entrega. |
| Git Flow completo, com branches `release/*` | Cerimônia desnecessária para um projeto individual sem releases paralelas. |
| *Squash merge* | Linha do tempo mais limpa, mas perde a granularidade dos commits revisados. |
| Usar apenas `feature/*` para as duas fases | Mistura a revisão da spec com a do código e dificulta ver quando a spec foi aprovada. |

## Consequências

**Positivas**

- Aprovação da spec e entrega do código ficam separadas e visíveis no histórico.
- `main` sempre corresponde a uma versão liberada.

**Negativas / riscos**

- Mais PRs por unidade (ao menos dois).
- Enquanto a proteção de branches não estiver ativa (incremento 1), a regra de não commitar direto depende de disciplina e das instruções do `CLAUDE.md`.
