# ADR-0001 — Registrar decisões arquiteturais com ADRs

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita, com apoio do Claude Code
- **Relacionados:** [05-processo-sdd.md](../05-processo-sdd.md)

## Contexto

No SDD, a documentação é a fonte da verdade, e isso inclui o **porquê** das escolhas, não só o **quê**. O projeto é individual e usa um agente de IA cujas sessões são efêmeras: sem registro, o raciocínio por trás de cada decisão se perde entre uma sessão e outra. A entrega do bootcamp também exige um registro sintético das decisões técnicas no README.

## Decisão

- Registrar toda decisão arquitetural em `docs/adr/NNNN-titulo.md`, no formato MADR simplificado em pt-BR: status, data, contexto, decisão, alternativas e consequências.
- ADRs aceitos são imutáveis. Uma mudança de decisão gera um novo ADR que substitui o anterior.
- O `README.md` mantém uma tabela sintética com todos os ADRs.
- O agente deve criar o ADR no mesmo PR da mudança ([CLAUDE.md](../../CLAUDE.md)).

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Registrar decisões apenas no README | Cresce sem estrutura e perde o contexto e as alternativas. |
| Wiki do GitHub | Fica fora do versionamento do código e dos PRs. |
| Não registrar | Decisões são rediscutidas e o agente perde o contexto. |

## Consequências

**Positivas**

- Histórico auditável das escolhas, revisado junto com o código.
- Contexto estável para o agente de IA em novas sessões.

**Negativas / riscos**

- Custo de escrita. Mitigado pelo formato curto e pelo template.
