# Relatórios de Execução dos Testes

Evidências versionadas da execução da suíte de testes. Estratégia em [07-estrategia-de-testes.md](../07-estrategia-de-testes.md#6-relatórios-e-evidências).

## Situação

| Relatório | Incremento | Resultado |
|-----------|------------|-----------|
| [2026-09-30-incremento-1.md](2026-09-30-incremento-1.md) | 1 — Fundação | 155 testes passaram, 5 de fumaça passaram, cobertura 96,18% |
| [2026-10-01-incremento-2.md](2026-10-01-incremento-2.md) | 2 — Contas e sessões | 266 testes passaram, cobertura 98% |
| [2026-10-01-incremento-3.md](2026-10-01-incremento-3.md) | 3 — Cofre de credenciais | 326 testes passaram, cobertura 99%, p95 de RNF-12 abaixo de 200 ms |
| [2026-10-03-incremento-4.md](2026-10-03-incremento-4.md) | 4 — Gerador e avaliador | 420 testes passaram, cobertura 99%, nenhum requisito *Must* sem teste |

Análises complementares: [relatório técnico-ético](relatorio-etico-tecnico.md) e [relato de experiência](relato-de-experiencia.md).

## Quando publicar

- Ao concluir cada incremento a partir do incremento 1 (obrigatório). O incremento 0 não tem código nem testes.
- Em PRs de implementação que alterem comportamento de segurança (recomendado).

## Nome do arquivo

`AAAA-MM-DD-incremento-N.md` (ex.: `2026-09-20-incremento-1.md`).

## Modelo

````markdown
# Relatório de execução — Incremento N

| Campo | Valor |
|-------|-------|
| Data | AAAA-MM-DD |
| Commit | `abcdef1` (branch `feature/NNN-slug`) |
| Ambiente | `docker compose run --rm tests` · Python 3.13.x · imagem `cofre-tests` |
| Comando | `uv run pytest` |

## Resumo

| Total | Passaram | Falharam | Pulados | Duração | Cobertura |
|------:|---------:|---------:|--------:|--------:|----------:|
| 0 | 0 | 0 | 0 | 0.0 s | 0% |

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 0 | ✅ |
| integration | 0 | ✅ |
| api | 0 | ✅ |
| security | 0 | ✅ |

## Rastreabilidade

| Requisito | Testes | Situação |
|-----------|-------:|----------|
| RF-01 | 0 | ✅ coberto |

Requisitos *Must* sem teste: nenhum.

## Log (trecho)

```text
<saída final do pytest, com o resumo e a tabela de cobertura>
```

## Observações

<falhas conhecidas, testes pulados e justificativa, refinamentos originados desta execução>
````
