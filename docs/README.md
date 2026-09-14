# Documentação do Cofre

A documentação é a **fonte da verdade** do projeto. Specs, planos, testes e código derivam dela, na ordem de precedência definida em [05-processo-sdd.md](05-processo-sdd.md#2-hierarquia-de-artefatos).

## Documentos de projeto

| # | Documento | Pergunta que responde |
|---|-----------|-----------------------|
| 01 | [Visão geral](01-visao-geral.md) | Que problema resolvemos, para quem e com que escopo? |
| 02 | [Requisitos](02-requisitos.md) | O que o sistema deve fazer e sob quais regras? |
| 03 | [Arquitetura](03-arquitetura.md) | Como o sistema está organizado e como a API se comporta? |
| 04 | [Segurança](04-seguranca.md) | Quais ameaças consideramos e como os dados são protegidos? |
| 05 | [Processo SDD](05-processo-sdd.md) | Como uma ideia vira spec, teste e código? |
| 06 | [Governança](06-governanca.md) | Como usamos Git, PRs, revisões, issues e releases? |
| 07 | [Estratégia de testes](07-estrategia-de-testes.md) | Como provamos que o sistema cumpre a spec? |
| 08 | [Ambiente e agentes](08-ambiente-e-agentes.md) | Como preparar o ambiente e como o Claude Code é usado? |
| 09 | [Roadmap](09-roadmap.md) | Em que ordem e em quais unidades o sistema é construído? |

## Registros

| Pasta ou arquivo | Conteúdo |
|------------------|----------|
| [adr/](adr/README.md) | Decisões arquiteturais (ADRs) |
| [registro-de-refinamentos.md](registro-de-refinamentos.md) | Mudanças na especificação motivadas por feedback |
| [sessoes/](sessoes/) | Resumos de sessões relevantes com o agente de IA |
| [relatorios/](relatorios/README.md) | Evidências de execução da suíte de testes |
| [glossario.md](glossario.md) | Termos do domínio e do processo |

## Artefatos fora de `docs/`

| Caminho | Conteúdo |
|---------|----------|
| [../.specify/memory/constitution.md](../.specify/memory/constitution.md) | Constituição: princípios inegociáveis |
| `../specs/NNN-*/` | Specs por unidade: `spec.md`, `plan.md`, `tasks.md`, `contracts/` (a partir do incremento 1) |
| [../CLAUDE.md](../CLAUDE.md) | Instruções do agente de IA |

## Como manter

- Todo documento começa com **Status**, **Versão** e **Última revisão**.
- Mudanças de conteúdo normativo (requisitos, arquitetura, segurança) entram por PR e, quando afetam o comportamento especificado, geram entrada no [registro de refinamentos](registro-de-refinamentos.md).
