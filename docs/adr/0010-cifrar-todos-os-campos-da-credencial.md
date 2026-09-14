# ADR-0010 — Cifrar todos os campos da credencial

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** RNF-01, RNF-12, RN-07, RF-09, RF-10, [03-arquitetura.md](../03-arquitetura.md#3-modelo-de-dados-conceitual)

## Contexto

Os metadados de uma credencial também são sensíveis: título e URL revelam quais serviços, bancos e sistemas o usuário usa. Por outro lado, a listagem precisa ordenar por título e a busca precisa filtrar por título, usuário e URL (RF-09, RF-10).

## Decisão

- Cifrar **todos** os campos da credencial (`title`, `username`, `password`, `url`, `notes`) juntos, como um único JSON em `ciphertext`.
- Manter em claro apenas `id`, `user_id`, `enc_version`, `created_at` e `updated_at`.
- **Listagem, ordenação, busca e paginação acontecem em memória**, depois de decifrar as credenciais do usuário da sessão.
- Limitar o cofre a **1.000 credenciais por usuário** (RN-07), mantendo previsível o custo dessas operações.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Cifrar apenas a senha | Permite busca e ordenação em SQL, mas expõe no banco quais serviços o usuário usa. |
| Índices cegos (HMAC dos campos) | Permitem apenas igualdade exata, não substring; aumentam a complexidade e ainda vazam padrões de repetição. |
| Uma coluna cifrada por campo | Mais nonces e mais operações, sem ganho, já que a busca continuaria em memória. |

## Consequências

**Positivas**

- Um vazamento do banco não revela nem mesmo quais serviços cada usuário guarda.
- Modelo simples: um texto cifrado por credencial.

**Negativas / riscos**

- Custo O(n) por listagem ou busca: decifrar até 1.000 itens, com meta de p95 < 200 ms (RNF-12).
- O limite de 1.000 credenciais é uma restrição de produto decorrente desta decisão.
- Não há como consultar metadados por SQL para relatórios.
