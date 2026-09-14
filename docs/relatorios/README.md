# Relatórios de Execução dos Testes

Evidências versionadas da execução da suíte de testes. Estratégia em [07-estrategia-de-testes.md](../07-estrategia-de-testes.md#6-relatórios-e-evidências).

## Situação

Nenhuma execução registrada ainda. O harness de testes é entregue no **incremento 1** ([09-roadmap.md](../09-roadmap.md)).

## Quando publicar

- Ao concluir cada incremento (obrigatório).
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
