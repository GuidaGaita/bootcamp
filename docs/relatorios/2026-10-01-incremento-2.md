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
| 266 | 266 | 0 | 0 | 19,0 s | 98% |

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 142 | ✅ |
| integration | 17 | ✅ |
| api | 93 | ✅ |
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
- Revisão assistida por IA (`/code-review`, esforço médio): 9 achados, todos tratados no [PR #69](https://github.com/GuidaGaita/bootcamp/pull/69). O `/security-review` não foi executado, por economia de tokens, apesar de o `CLAUDE.md` exigi-lo para `crypto` e autenticação.

## Achados da revisão

| # | Achado | Tratamento |
|---|--------|------------|
| 1 | O controle de tentativas não era atômico: logins em paralelo liam o mesmo contador e ultrapassavam o limite de 5 (RN-14, RN-16) | Corrigido: a tentativa é contada antes da verificação, por um upsert atômico; teste com 24 logins paralelos admite no máximo 5 palpites. Refinamento R-026 |
| 2 | Duas primeiras falhas simultâneas geravam `IntegrityError` (500) | Corrigido pelo mesmo upsert |
| 3 | `login_throttles` crescia sem limite com e-mails inexistentes | Mitigado: linhas ociosas há 24 h e sem bloqueio são apagadas. O ritmo de inserção ainda não é limitado (risco aceito: exigiria limite por origem) |
| 4 | O hash fictício era calculado no primeiro login com e-mail inexistente (tempo diferente) | Corrigido: calculado ao criar a aplicação |
| 5 | Campos de senha e e-mail sem limite de tamanho no cadastro, troca e exclusão | Corrigido: limites estruturais de 1024 e 320 caracteres |
| 6 | A nova senha era validada antes de checar o bloqueio, e a resposta podia ser 422 em vez de 429 | Mantido de propósito: validar a entrada do próprio chamador não verifica a senha atual, e uma requisição malformada não deve consumir uma tentativa |
| 7 | Aleatoriedade não injetável | Mantido: docs/03 §5 prevê a fonte injetável só para o gerador de senhas (unidade 004) |
| 8 | Tripla do Argon2id duplicada | Corrigido: `Settings.argon2_cost` |
| 9 | 401 sem `WWW-Authenticate: Bearer` | Corrigido |
