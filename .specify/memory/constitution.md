# Cofre Constitution

Princípios inegociáveis do projeto **Cofre**, uma API REST de gerenciamento de senhas. Todo plano gerado por `/speckit-plan` passa pelo *Constitution Check* contra este documento.

## Core Principles

### I. Especificação como fonte da verdade (NÃO NEGOCIÁVEL)

- Nenhum código de produção é escrito sem uma spec **Aprovada** (PR de spec mergeado em `develop`) com `plan.md` e `tasks.md`.
- Quando teste, revisão ou implementação revelam divergência, corrige-se **primeiro a spec** (seção *Histórico de revisões* e `docs/registro-de-refinamentos.md`), depois os testes e só então o código.
- Precedência em caso de conflito: esta constituição → `docs/` → `spec.md` → `plan.md` → `tasks.md` → código.

**Justificativa:** o projeto existe para demonstrar SDD. Uma spec que não governa o código é só documentação decorativa.

### II. Segurança por padrão (NÃO NEGOCIÁVEL)

- `docs/04-seguranca.md` é normativo: nenhum plano ou código pode contradizê-lo.
- Nenhum dado de credencial, senha mestra, token ou chave em texto claro no banco, em logs, em mensagens de erro ou em respostas, salvo as exceções explícitas de RF-11 e RF-14.
- Criptografia apenas com `cryptography` e `argon2-cffi`; aleatoriedade apenas com `secrets`/`os.urandom`; nenhuma primitiva própria.
- Toda consulta a dados de usuário filtra pelo usuário da sessão; recurso alheio responde 404.
- Mudanças em algoritmos, parâmetros mínimos ou fluxo de chaves exigem ADR.

**Justificativa:** um gerenciador de senhas inseguro é pior do que nenhum.

### III. Testes primeiro e rastreáveis (NÃO NEGOCIÁVEL)

- TDD: o teste de aceitação ou de borda é escrito e **falha** antes da implementação.
- Todo cenário de aceitação e todo caso de borda de uma spec vira teste automatizado marcado com `@pytest.mark.req("<IDs>")`.
- Suíte verde e cobertura ≥ 85% são pré-requisitos de merge.
- Testes são determinísticos: relógio e aleatoriedade injetáveis, sem rede externa, sem dependência de ordem.

**Justificativa:** o teste é a prova executável de que a spec foi cumprida.

### IV. Unidades isoladas e contratos explícitos

- Cada unidade do roadmap é especificada, implementada, testada e entregue de forma independente.
- Camadas `api → services → (crypto, repositories) → core`; nenhuma camada depende de outra acima dela e `services` não conhece HTTP.
- Contratos de API (`contracts/`) são definidos no plano, **antes** da implementação, e usam o formato de erro padronizado de `docs/03-arquitetura.md`.
- Mudança incompatível de contrato exige versão MAJOR da spec.

**Justificativa:** isolamento permite desenvolvimento iterativo e testes focados.

### V. Simplicidade

- Um processo, um banco (SQLite), nenhum serviço adicional sem ADR.
- YAGNI: implementar apenas o que a spec pede. Toda dependência nova é justificada no `research.md` da unidade.
- Complexidade extra precisa ser registrada e justificada na seção *Complexity Tracking* do plano.

**Justificativa:** o escopo é um gerenciador de senhas **simples**; cada peça a mais é superfície de erro.

## Restrições Técnicas

- Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 com SQLite, `uv`, `pytest`, `ruff`, Docker.
- API JSON versionada em `/api/v1`, com especificação OpenAPI publicada.
- Documentação e specs em pt-BR; identificadores de código em inglês (ADR-0002).
- Único agente de IA: Claude Code, orientado por `CLAUDE.md` (ADR-0003).

## Fluxo de Desenvolvimento e Quality Gates

- Processo em `docs/05-processo-sdd.md`; governança em `docs/06-governanca.md`.
- Proibido commit direto em `main` e `develop`; toda mudança entra por PR revisado, com merge commit.
- Gates para merge:
  1. `ruff check` e `ruff format --check` sem erros;
  2. `pytest` verde com cobertura ≥ 85%;
  3. *Constitution Check* aprovado no plano da unidade;
  4. `/speckit-analyze` sem achados críticos (PRs de spec);
  5. todos os comentários de revisão tratados.
- Toda decisão arquitetural gera ADR em `docs/adr/` e entra na tabela do `README.md`.

## Governance

- Esta constituição prevalece sobre qualquer outro artefato ou prática do projeto.
- Emendas são feitas em PR próprio, com justificativa, atualização dos artefatos dependentes (templates, `CLAUDE.md`, `docs/`) e incremento de versão:
  - **MAJOR:** remoção ou redefinição incompatível de um princípio;
  - **MINOR:** novo princípio ou seção;
  - **PATCH:** esclarecimento de redação.
- Todo PR verifica a conformidade pelo checklist do template.
- Orientações operacionais para o agente ficam em `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-09-13 | **Last Amended**: 2026-09-13
