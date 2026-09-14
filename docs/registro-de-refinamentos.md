# Registro de Refinamentos da Especificação

Histórico das alterações na especificação motivadas por feedback: sessões de descoberta, revisões de PR, testes e implementação. Cada spec mantém também o próprio **Histórico de revisões**; este arquivo consolida o que mudou no projeto como um todo.

Procedimento em [05-processo-sdd.md](05-processo-sdd.md#5-refinamento-por-feedback).

| ID | Data | Artefato afetado | Proposta ou versão anterior | Como ficou | Motivo | Origem | Referência |
|----|------|------------------|-----------------------------|------------|--------|--------|------------|
| R-001 | 2026-09-13 | Arquivos de instrução de agentes | `AGENTS.md` como fonte canônica + `CLAUDE.md` importando | Apenas `CLAUDE.md` | Somente o Claude Code será usado | Sessão grill-me (Q7) | [ADR-0003](adr/0003-claude-code-como-agente-unico.md) |
| R-002 | 2026-09-13 | Estrutura SDD | Estrutura própria e leve inspirada no Spec Kit | GitHub Spec Kit 1.0.6 | Preferência do mantenedor | Sessão grill-me (Q8) | [ADR-0004](adr/0004-sdd-com-github-spec-kit.md) |
| R-003 | 2026-09-13 | Processo de revisão | Papéis rotativos entre membros da equipe | Autorrevisão + revisão assistida por IA publicada no PR | Projeto individual; o GitHub não permite autoaprovação | Sessão grill-me (Q3) | [ADR-0012](adr/0012-revisao-de-codigo-em-projeto-individual.md) |
| R-004 | 2026-09-13 | Planejamento | Sprints de 1 semana com escopo por data | Incrementos sem data, um milestone cada | Mantenedor descartou cronograma | Sessão grill-me (Q4) | [09-roadmap.md](09-roadmap.md) |
| R-005 | 2026-09-13 | Idioma | Mensagens de commit em inglês | Tipo Conventional Commits em inglês e descrição em pt-BR | Mantenedor escolheu pt-BR | Sessão grill-me (Q1) | [ADR-0002](adr/0002-idioma-da-documentacao-e-do-codigo.md) |
| R-006 | 2026-09-13 | Fluxo Git | Branches `main`, `develop`, `feature/*` | Acrescentado o prefixo `spec/*` para a Fase A de cada unidade | Separar a revisão da spec da revisão da implementação | Decisão delegada ao agente | [ADR-0011](adr/0011-fluxo-git.md) |
| R-007 | 2026-09-13 | RN-14 ([02](02-requisitos.md)), modelo de dados ([03](03-arquitetura.md)), A2/A3 e ciclo de login ([04](04-seguranca.md)), casos de borda ([07](07-estrategia-de-testes.md)) | Contador de falhas e bloqueio na tabela `users`, ou seja, apenas para contas cadastradas | Tabela `login_throttles` indexada pelo SHA-256 do e-mail normalizado; bloqueio idêntico para e-mails cadastrados ou não | O 429 só aconteceria para contas reais, permitindo enumerar e-mails, o que contradiz RN-04 | Revisão assistida por IA do PR #1 (achado 1) | [PR #1](https://github.com/GuidaGaita/bootcamp/pull/1) |
