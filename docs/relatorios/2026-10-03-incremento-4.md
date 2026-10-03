# Relatório de execução — Incremento 4

| Campo | Valor |
|-------|-------|
| Data | 2026-10-03 |
| Commit | branch `feature/004-gerador-de-senhas` |
| Ambiente | `uv run pytest` local (Windows 11, Python 3.13.5); CI e `docker compose run --rm tests` no PR |
| Comando | `pytest` (seleção padrão com gate de 85%) |

## Resumo

| Total | Passaram | Falharam | Pulados | Duração | Cobertura (linhas + ramificações) |
|------:|---------:|---------:|--------:|--------:|----------:|
| 413 | 413 | 0 | 0 | 27 s | 99% |

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 203 | ✅ |
| integration | 17 | ✅ |
| api | 168 | ✅ |
| security | 25 | ✅ |
| perf | 1 | execução separada; não alterado nesta unidade |
| smoke | 5 | execução separada; não alterados nesta unidade |

## Rastreabilidade

Extraído de `reports/rastreabilidade.md` da suíte padrão.

| Requisito | Testes | Situação |
|-----------|-------:|----------|
| RF-14 | 34 | ✅ |
| RF-15 | 56 | ✅ |
| RN-10 | 31 | ✅ |
| RN-11 | 53 | ✅ |
| RNF-05 | 49 | ✅ |
| RNF-04 | 67 | ✅ |

**Requisitos *Must* sem teste: nenhum.** Todos os requisitos *Must* do projeto (RF-01 a RF-04, RF-08, RF-09, RF-11 a RF-14 e RNF-01 a RNF-11 aplicáveis) têm ao menos um teste aprovado. Só o RF-16 (*Could*, unidade 005) não foi implementado.

## Observações

- A cobertura dos três arquivos novos (`services/passwords.py`, esquemas e roteador) é de 100%, e o avaliador foi especificado de forma determinística para ser testável (limites de pontuação, tempo de quebra e cada sugestão têm teste).
- O gerador cumpre RN-10 em 1.000 gerações, com e sem `exclude_ambiguous`, e em comprimento 8 com os quatro conjuntos; a fonte aleatória injetável permite um teste determinístico, e o `secrets` é a fonte padrão (nenhum `import random` em `src/`, verificado por teste).
- Na primeira execução, um teste falhou por defeito do próprio teste: `123456789` está na lista de senhas comuns, que tem precedência sobre a regra de sequência, conforme a spec. O teste foi corrigido, e o código de produção não mudou. Durante a escrita dos testes foi removida uma asserção vacuamente verdadeira (`... or True`) antes da primeira execução.
- O avaliador é uma heurística própria, sem dependência nova (decisão da spec): é menos preciso que uma biblioteca de estimativa e a lista de senhas comuns é pequena. Serve de indicador, não de garantia.
- Fluxo enxuto, sem `/speckit-*`. Revisão assistida por IA: ver os comentários do PR de implementação.
