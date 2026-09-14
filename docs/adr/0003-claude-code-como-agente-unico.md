# ADR-0003 — Claude Code como único agente de IA

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita
- **Relacionados:** [08-ambiente-e-agentes.md](../08-ambiente-e-agentes.md), [Sessão grill-me Q7](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [R-001](../registro-de-refinamentos.md)

## Contexto

A entrega exige ao menos uma ferramenta de IA configurada e documentada, com os arquivos de instrução versionados. Cada ferramenta lê um arquivo diferente (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`), e manter vários arquivos duplica regras que acabam divergindo. O projeto tem um único mantenedor, que usará apenas o Claude Code.

## Decisão

- **Claude Code** é o único agente de IA do projeto.
- As instruções ficam em **`CLAUDE.md`**, na raiz. Não haverá `AGENTS.md`, `.cursorrules` nem equivalentes.
- As skills usadas ficam versionadas em `.claude/skills/`: as do Spec Kit (`speckit-*`) e as de `mattpocock/skills` (`grill-me`, `grilling`).
- Commits feitos com apoio do agente levam o rodapé `Co-Authored-By`.
- Sessões com decisões relevantes são resumidas em `docs/sessoes/`.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| `AGENTS.md` canônico + `CLAUDE.md` importando | Útil com várias ferramentas. Sem outras ferramentas, só adiciona indireção. |
| Cursor, Codex CLI ou Antigravity | O mantenedor escolheu o Claude Code; a integração com o Spec Kit via skills é nativa. |

## Consequências

**Positivas**

- Uma única fonte de instruções, sem duplicação.
- O uso do agente fica auditável pelos commits co-assinados, pelas sessões registradas e pelas revisões nos PRs.

**Negativas / riscos**

- Adotar outra ferramenta no futuro exigirá um novo ADR e, provavelmente, a criação de um `AGENTS.md`.
