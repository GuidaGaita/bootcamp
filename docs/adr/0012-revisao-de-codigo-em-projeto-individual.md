# ADR-0012 — Revisão de código em projeto individual

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [06-governanca.md §4](../06-governanca.md#4-revisão-de-código-em-projeto-individual), [Sessão grill-me Q3](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [R-003](../registro-de-refinamentos.md)

## Contexto

A entrega pede PRs com histórico de revisões, comentários e aprovações entre membros. O projeto tem um único mantenedor, e o GitHub não permite aprovar o próprio PR. Mesmo assim, é preciso uma revisão real, que encontre problemas, e não uma aprovação cerimonial.

## Decisão

Todo PR passa por um processo de revisão registrado no próprio PR:

1. **Autorrevisão:** o autor percorre o diff e marca o checklist do template.
2. **Revisão assistida por IA:** o Claude Code revisa o PR e publica os achados como comentários de revisão.
   - PRs de código: `/code-review` com `--comment`.
   - PRs que tocam `crypto`, autenticação ou sessões: também `/security-review`.
   - PRs de documentação: revisão dirigida de consistência entre documentos, requisitos e ADRs.
3. **Tratamento:** cada comentário é respondido, corrigido com o commit referenciado ou justificado.
4. **Merge** somente com todos os comentários tratados.

A proteção de branch exige **0 aprovações** enquanto o projeto for individual e passa a exigir **1 aprovação humana** se entrarem colaboradores.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Criar uma segunda conta no GitHub para aprovar | Simula uma revisão que não aconteceu e viola os termos de uso do GitHub. |
| Dispensar a revisão | Perde a verificação independente e a evidência exigida. |
| Pedir revisão a colegas de forma ocasional | Não é garantida para todos os PRs; pode complementar, mas não substituir. |

## Consequências

**Positivas**

- Histórico de revisão real e auditável em todo PR.
- A revisão por IA verifica conformidade com a spec, a constituição e as regras de segurança.

**Negativas / riscos**

- Revisão por IA **não equivale** a aprovação humana independente; a limitação fica explícita na documentação.
- Achados da IA podem ser falsos positivos. O autor justifica quando discorda, e essa justificativa também fica registrada.
