# ADR-0007 — SQLite com SQLAlchemy 2

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [03-arquitetura.md](../03-arquitetura.md#3-modelo-de-dados-conceitual)

## Contexto

O Cofre roda como instância única, com volume de dados pequeno (até 1.000 credenciais por usuário) e foco em simplicidade. Precisa de transações, integridade referencial e testes rápidos e isolados.

## Decisão

- Banco **SQLite**, em arquivo no volume Docker `cofre-data`.
- Acesso via **SQLAlchemy 2.0** (ORM, modo síncrono), encapsulado na camada `repositories`.
- Chaves estrangeiras habilitadas (`PRAGMA foreign_keys=ON`), com exclusão em cascata de sessões e credenciais.
- Schema criado com `metadata.create_all` no MVP. O **Alembic** entra na primeira mudança de schema após uma release.
- Nos testes, um SQLite novo em diretório temporário para cada teste.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| PostgreSQL | Mais um serviço no compose e mais complexidade operacional, sem necessidade real no MVP. |
| Arquivo JSON | Sem transações, sem concorrência segura, sem integridade referencial. |
| `sqlite3` puro | Mais código repetitivo e sem caminho fácil para trocar de banco. |

## Consequências

**Positivas**

- Zero infraestrutura extra; testes rápidos e isolados.
- A migração para PostgreSQL exige basicamente trocar `COFRE_DATABASE_URL`.

**Negativas / riscos**

- Concorrência de escrita limitada; adequado apenas para instância única.
- O arquivo do banco é um alvo concentrado, mitigado pela cifragem integral ([ADR-0008](0008-criptografia-em-envelope.md), [ADR-0010](0010-cifrar-todos-os-campos-da-credencial.md)).
