# Relatório de execução — Incremento 3

| Campo | Valor |
|-------|-------|
| Data | 2026-10-01 |
| Commit | branch `feature/003-cofre-de-credenciais` |
| Ambiente | `uv run pytest` local (Windows 11, Python 3.13.5); CI e `docker compose run --rm tests` no PR |
| Comando | `pytest` (seleção padrão com gate de 85%) e `pytest -m perf --no-cov` |

## Resumo

| Total | Passaram | Falharam | Pulados | Duração | Cobertura (linhas + ramificações) |
|------:|---------:|---------:|--------:|--------:|----------:|
| 326 | 326 | 0 | 0 | 95 s (36 a 95 s em execuções diferentes, por carga da máquina) | 99% |

## Por nível

| Marcador | Testes | Resultado |
|----------|-------:|-----------|
| unit | 142 | ✅ |
| integration | 17 | ✅ |
| api | 145 | ✅ |
| security | 22 | ✅ |
| perf | 1 | ✅ (execução separada) |
| smoke | 5 | execução separada; não alterados nesta unidade |

## Desempenho (RNF-12)

Cofre com 990 credenciais de cerca de 1 KB cada (mais as criadas durante a medição), 20 amostras por operação, p95 em segundos pelo cliente HTTP de teste, na máquina do mantenedor:

| Operação | p95, 1ª execução | p95, 2ª execução (máquina mais carregada) | Meta |
|----------|----:|----:|-----:|
| Criar | 0,014 | 0,016 | < 0,200 |
| Listar (100 itens, decifrando o cofre inteiro) | 0,089 | 0,131 | < 0,200 |
| Buscar | 0,033 | 0,046 | < 0,200 |
| Consultar | 0,007 | 0,012 | < 0,200 |
| Atualizar | 0,012 | 0,018 | < 0,200 |

## Rastreabilidade

Extraído de `reports/rastreabilidade.md`.

| Requisito | Testes | Situação |
|-----------|-------:|----------|
| RF-08 | 20 | ✅ |
| RF-09 | 7 | ✅ |
| RF-10 | 6 | ✅ |
| RF-11 | 10 | ✅ |
| RF-12 | 13 | ✅ |
| RF-13 | 6 | ✅ |
| RN-06 / RN-07 / RN-08 / RN-09 | 15 / 1 / 2 / 6 | ✅ |
| RN-13 / RN-15 | 6 / 1 | ✅ |
| RNF-01 / RNF-03 / RNF-04 | 35 / 13 / 63 | ✅ |

Requisitos *Must* sem teste: só o RF-14 (unidade 004).

## Observações

- Todos os testes foram escritos antes da implementação e vistos falhando; a primeira execução completa terminou com 2 falhas, ambas defeitos do próprio teste (verificação de "valor não ecoado" aplicada a uma string vazia), corrigidos sem mudar o código de produção.
- A cobertura das camadas novas (`vault`, repositório, rotas e esquemas de credenciais) é de 100%.
- Segurança verificada por teste: nenhum campo da credencial no arquivo SQLite; `ciphertext` adulterado, truncado ou copiado entre linhas e entre usuários falha com 500 genérico; cada cifragem usa nonce novo; criar, atualizar e listar nunca devolvem a senha; nada vaza para logs.
- A exclusão de conta passou a apagar também as credenciais (RN-12), com teste.
- A suíte levou 36 s e 78 s em duas execuções no mesmo código; o critério de 60 s da spec 001 (SC-006) depende da carga da máquina. O CI é a referência.
- Fluxo enxuto, sem `/speckit-*` (ver `docs/sessoes/2026-09-30-fase-a-unidades-002-003.md`). Revisão assistida por IA: ver os comentários do PR de implementação.

## Achados da revisão

A revisão assistida por IA (`/code-review`, esforço médio) achou 9 problemas, todos tratados e comentados no [PR #70](https://github.com/GuidaGaita/bootcamp/pull/70). Os mais relevantes:

- **Corrida no limite do cofre e no `PATCH`.** Verificar a contagem e depois inserir, e ler-mesclar-recifrar o blob, permitiam passar do limite de 1.000 credenciais e perder alterações de `PATCH` paralelos. As escritas de cada usuário passaram a ser serializadas pelo bloqueio de escrita do SQLite; os dois testes de regressão **falham sem o bloqueio** e passam com ele. É o mesmo padrão da corrida do bloqueio de login (R-026), na unidade 002.
- **URL validada diferente da guardada.** `urlsplit` ignora espaços e quebras de linha; URLs assim passavam e eram armazenadas como vieram. Passaram a ser rejeitadas.
- **Falha de integridade sem log.** Agora gera um evento ERROR com o `id` da credencial, sem dados.
- Dois testes frouxos (um `PATCH` sem corpo e uma asserção `A or B`) foram reforçados.
- O `/security-review` não foi executado, por economia de tokens.
