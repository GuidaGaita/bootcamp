# ADR-0016 — Testes de contrato contra o OpenAPI da spec

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [spec 001](../../specs/001-fundacao-da-api/spec.md), [research R13](../../specs/001-fundacao-da-api/research.md), RNF-08, [ADR-0013](0013-harness-de-testes-com-pytest.md), constituição (princípio IV)

## Contexto

A constituição exige contratos de API definidos em `specs/NNN-*/contracts/` **antes** da implementação, e RNF-08 é verificado por "testes de contrato". O FastAPI gera `/openapi.json` a partir do código, e comparar a aplicação só com o que ela mesma gera não prova conformidade com a spec aprovada.

## Decisão

- Cada unidade mantém o contrato em `specs/NNN-*/contracts/openapi.yaml` (OpenAPI 3.1).
- Os testes de API validam **status, cabeçalhos obrigatórios e corpo** de cada resposta contra esse arquivo, com `jsonschema` (Draft 2020-12) e `pyyaml`, por meio de um utilitário único em `tests/support/contract.py`.
- Um teste verifica que `/openapi.json` da aplicação declara todas as operações e status do contrato, sem exigir igualdade textual.
- Respostas transversais de `/api/v1` ficam em `components/responses` e na extensão `x-cofre-api-v1`, reutilizadas pelos contratos das unidades seguintes.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Comparar `/openapi.json` com o arquivo inteiro | Frágil: o FastAPI inclui detalhes gerados que não são contrato. |
| `schemathesis` | Gera casos próprios e acopla a suíte a outra ferramenta; pesado para o escopo. |
| `openapi-core` | Mais uma camada de abstração para o que `jsonschema` já resolve. |
| Só asserções manuais nos testes | O contrato poderia divergir da implementação sem que nenhum teste percebesse. |

## Consequências

**Positivas**

- Mudança de contrato sem atualizar a spec quebra a suíte: a spec continua sendo a fonte da verdade.
- O mesmo utilitário serve às unidades 002 a 005.

**Negativas / riscos**

- Os testes dependem do caminho de `specs/`, que também precisa ir para a imagem de testes.
- Esquemas com `if/then/else` e `allOf` exigem cuidado para manter mensagens de falha legíveis.
