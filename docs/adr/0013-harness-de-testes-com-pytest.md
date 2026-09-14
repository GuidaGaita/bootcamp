# ADR-0013 — Harness de testes com pytest e rastreabilidade

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [07-estrategia-de-testes.md](../07-estrategia-de-testes.md), RNF-09

## Contexto

A entrega exige um harness que valide a aplicação conforme a especificação, uma suíte com cenários principais e casos de borda, e evidências de execução. No SDD, cada teste precisa ser rastreável até o requisito que verifica.

## Decisão

- **pytest** + **pytest-cov** como base, com configuração em `pyproject.toml` e `--strict-markers`.
- **Marcadores de nível:** `unit`, `integration`, `api`, `security`, `smoke`.
- **Marcador de rastreabilidade** `@pytest.mark.req("RF-xx", ...)`, obrigatório em testes de aceitação e de borda. Um *hook* valida o formato dos IDs e gera `reports/rastreabilidade.md`.
- **Determinismo:** `FakeClock` injetável e parâmetros de Argon2id reduzidos apenas com `COFRE_ENV=test`.
- **Gate:** cobertura de linhas e *branches* ≥ 85% no pacote `cofre`.
- **Evidências:** artefatos em `reports/` (JUnit, cobertura, log) publicados no CI; relatório versionado em `docs/relatorios/` a cada incremento.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| `unittest` | Mais verboso; fixtures e marcadores menos expressivos. |
| `pytest-bdd` / `behave` (Gherkin) | Aproxima dos cenários *Given/When/Then*, mas duplica a spec em arquivos `.feature` e acrescenta uma camada de manutenção. |
| Sem marcador de rastreabilidade | Não haveria como provar automaticamente quais requisitos têm teste. |

## Consequências

**Positivas**

- Relação requisito → teste gerada automaticamente, usada para manter a matriz de rastreabilidade.
- Suíte rápida e determinística, adequada para rodar a cada PR.

**Negativas / riscos**

- Disciplina para marcar os testes, reforçada pelo checklist do PR e pelo relatório de requisitos *Must* sem teste.
- Parâmetros reduzidos em teste não exercitam o custo real do Argon2id; um teste de desempenho separado cobre RNF-12.
