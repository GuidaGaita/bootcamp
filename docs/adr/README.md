# Architecture Decision Records (ADRs)

Registro das decisões arquiteturais do Cofre, no formato **MADR simplificado** em pt-BR ([ADR-0001](0001-registrar-decisoes-com-adrs.md)).

## Como registrar uma decisão

1. Copie o [template](template.md) para `NNNN-titulo-em-kebab-case.md`, usando o próximo número livre.
2. Preencha contexto, decisão, alternativas e consequências. O texto deve ser curto e objetivo.
3. Adicione a decisão ao índice abaixo e à tabela de ADRs do [README principal](../../README.md#decisões-arquiteturais-adrs).
4. Inclua o ADR no mesmo PR da mudança que ele justifica.

**ADRs aceitos não são editados** (exceto correções de redação). Para mudar uma decisão, crie um novo ADR e marque o anterior como `Substituída por ADR-NNNN`.

**Status possíveis:** `Proposta` · `Aceita` · `Rejeitada` · `Obsoleta` · `Substituída por ADR-NNNN`.

## Índice

| ADR | Título | Status | Data |
|-----|--------|--------|------|
| [0001](0001-registrar-decisoes-com-adrs.md) | Registrar decisões arquiteturais com ADRs | Aceita | 2026-09-13 |
| [0002](0002-idioma-da-documentacao-e-do-codigo.md) | Idioma da documentação e do código | Aceita | 2026-09-13 |
| [0003](0003-claude-code-como-agente-unico.md) | Claude Code como único agente de IA | Aceita | 2026-09-13 |
| [0004](0004-sdd-com-github-spec-kit.md) | SDD com GitHub Spec Kit | Aceita | 2026-09-13 |
| [0005](0005-api-rest-multiusuario-sem-frontend.md) | API REST multiusuário sem frontend | Aceita | 2026-09-13 |
| [0006](0006-python-fastapi-uv.md) | Python 3.13 + FastAPI + uv | Aceita | 2026-09-13 |
| [0007](0007-sqlite-com-sqlalchemy.md) | SQLite com SQLAlchemy 2 | Aceita | 2026-09-13 |
| [0008](0008-criptografia-em-envelope.md) | Criptografia em envelope com Argon2id e AES-256-GCM | Aceita | 2026-09-13 |
| [0009](0009-sessoes-com-token-opaco.md) | Sessões com token opaco em vez de JWT | Aceita | 2026-09-13 |
| [0010](0010-cifrar-todos-os-campos-da-credencial.md) | Cifrar todos os campos da credencial | Aceita | 2026-09-13 |
| [0011](0011-fluxo-git.md) | Fluxo Git com `main`, `develop` e branches de trabalho | Aceita | 2026-09-13 |
| [0012](0012-revisao-de-codigo-em-projeto-individual.md) | Revisão de código em projeto individual | Aceita | 2026-09-13 |
| [0013](0013-harness-de-testes-com-pytest.md) | Harness de testes com pytest e rastreabilidade | Aceita | 2026-09-13 |
| [0014](0014-ambiente-reprodutivel-com-docker.md) | Ambiente reprodutível com Docker Compose e GitHub Actions | Aceita | 2026-09-13 |
