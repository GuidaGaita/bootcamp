# ADR-0004 — SDD com GitHub Spec Kit

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita (ferramenta); Claude Code (configuração, por delegação)
- **Relacionados:** [05-processo-sdd.md](../05-processo-sdd.md), [Sessão grill-me Q8](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [R-002](../registro-de-refinamentos.md)

## Contexto

O projeto adota Specification-Driven Development e precisa de uma estrutura padronizada de especificações (requisitos, plano técnico, contratos, tarefas) integrada ao agente de IA. Havia quatro opções: GitHub Spec Kit, estilo Kiro, OpenSpec ou uma estrutura própria.

## Decisão

Usar o **GitHub Spec Kit 1.0.6**, inicializado com:

```bash
specify init --here --force --non-interactive --integration claude --script py
```

Configuração adotada:

| Aspecto | Escolha | Motivo |
|---------|---------|--------|
| Integração | Claude Code em modo **skills** (`.claude/skills/speckit-*`) | Padrão do Spec Kit para o Claude |
| Scripts | **Python** (`.specify/scripts/python/`) | Portáveis entre Windows (desenvolvimento), Linux (container) e CI |
| Extensão `git` | **Não instalada** | O fluxo de branches do projeto ([ADR-0011](0011-fluxo-git.md)) usa `spec/` e `feature/`; a extensão criaria branches `NNN-slug` fora do padrão |
| Numeração | Sequencial, com `NNN` igual ao número da unidade do roadmap | Mapeamento direto entre roadmap e specs |
| Fases | Dois PRs por unidade: spec (Fase A) e implementação (Fase B) | A spec é revisada e aprovada antes de qualquer código |
| Constituição | Escrita diretamente em `.specify/memory/constitution.md` | Consolida os princípios definidos na documentação |

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Estrutura própria inspirada no Spec Kit | Mais controle, mas sem comandos de apoio (`clarify`, `analyze`, `converge`). |
| Estilo Kiro (`requirements`/`design`/`tasks` com EARS) | Sem tooling equivalente para o Claude Code. |
| OpenSpec (propostas em delta) | Mais cerimônia do que o projeto precisa. |

## Consequências

**Positivas**

- Fluxo guiado por comandos, com verificações de consistência (`/speckit-analyze`, `/speckit-converge`) e *Constitution Check* nos planos.
- Artefatos padronizados e reconhecíveis.

**Negativas / riscos**

- Dependência da versão da CLI. Mitigação: versão fixada e processo de atualização documentado em [08-ambiente-e-agentes.md](../08-ambiente-e-agentes.md#55-atualização-das-ferramentas).
- Templates em inglês (ver [ADR-0002](0002-idioma-da-documentacao-e-do-codigo.md)).
- Arquivos gerados não devem ser editados à mão, porque seriam sobrescritos em atualizações.
