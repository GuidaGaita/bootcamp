# ADR-0002 — Idioma da documentação e do código

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita
- **Relacionados:** [Sessão grill-me Q1](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [R-005](../registro-de-refinamentos.md)

## Contexto

O projeto é avaliado em português, mas o ecossistema técnico (Python, bibliotecas, convenções como Conventional Commits) e os templates do Spec Kit estão em inglês. Misturar idiomas sem regra gera inconsistência.

## Decisão

| Artefato | Idioma |
|----------|--------|
| `docs/`, specs, planos, tarefas, ADRs, `CLAUDE.md`, `README.md`, issues e PRs | **pt-BR** |
| Descrição das mensagens de commit | **pt-BR** (o tipo Conventional Commits permanece em inglês: `feat`, `fix`...) |
| Identificadores de código, nomes de testes, docstrings e comentários | **Inglês** |
| `code` dos erros da API | **Inglês** (ex.: `INVALID_CREDENTIALS`) |
| `message` dos erros da API | **pt-BR** |
| Títulos de seção dos templates do Spec Kit | **Inglês** (os comandos dependem deles) |
| Slugs de branch | pt-BR sem acentos, em kebab-case |

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Tudo em pt-BR, inclusive o código | Identificadores em português se misturam às APIs das bibliotecas, em inglês, e dificultam a leitura. |
| Tudo em inglês | Atrito na avaliação e na leitura pelo mantenedor. |

## Consequências

**Positivas**

- Documentação acessível para a avaliação; código idiomático.

**Negativas / riscos**

- Specs em pt-BR sob títulos de seção em inglês ficam com aparência mista. É aceitável pela compatibilidade com o Spec Kit.
