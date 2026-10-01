# Relatório de execução — Incremento 2

| Campo | Valor |
|-------|-------|
| Data | 2026-10-01 |
| Commit | branch `feature/002-contas-e-sessoes` |
| Ambiente | `uv run pytest` local (Windows 11, Python 3.13.5); CI e `docker compose run --rm tests` no PR |
| Comando | `pytest` (seleção padrão com gate de 85%) |

## Resumo

| Total | Passaram | Falharam | Pulados | Duração | Cobertura (linhas + ramificações) |
|------:|---------:|---------:|--------:|--------:|----------:|
| 256 | 256 | 0 | 0 | 16,8 s | 98% |

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 142 | ✅ |
| integration | 9 | ✅ |
| api | 91 | ✅ |
| security | 14 | ✅ |
| smoke | 5 | execução separada; não alterados nesta unidade |

## Rastreabilidade

Extraído de `reports/rastreabilidade.md`.

| Requisito | Testes | Situação |
|-----------|-------:|----------|
| RF-02 | 9 | ✅ |
| RF-03 | 4 | ✅ |
| RF-04 | 2 | ✅ |
| RF-05 | 2 | ✅ |
| RF-06 | 7 | ✅ |
| RF-07 | 5 | ✅ |
| RN-01 / RN-02 | 25 / 27 | ✅ |
| RN-04 / RN-05 | 3 / 14 | ✅ |
| RN-12 | 2 | ✅ |
| RN-14 / RN-16 | 5 / 6 | ✅ |
| RNF-02 / RNF-05 / RNF-06 / RNF-07 | 36 / 29 / 29 / 2 | ✅ |
| RNF-04 | 53 | ✅ |

Requisitos *Must* sem teste: só os das unidades 003 a 005 (RF-08, RF-09, RF-11 a RF-14, RNF-01, RNF-03).

## Observações

- A primeira execução completa da suíte passou sem correções de código. O `ruff` apontou falsos positivos (`S105`, `S608`) para senhas e SQL fixos nos **testes**, resolvidos ignorando essas regras só em `tests/**`.
- Os testes foram escritos antes da implementação e vistos falhando no pacote `crypto` e na validação; os das histórias 2 e 3 foram escritos antes do código, mas todos os arquivos de implementação entraram no mesmo commit.
- O fluxo de spec foi enxuto, sem `/speckit-*` (ver `docs/sessoes/2026-09-30-fase-a-unidades-002-003.md`).
- Revisão assistida por IA (`/code-review` e `/security-review`): ver os comentários do PR de implementação.
