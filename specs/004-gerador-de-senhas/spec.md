# Feature Specification: Gerador e avaliador de senhas

**Feature Branch**: `spec/004-gerador-de-senhas`

**Created**: 2026-10-03

**Status**: Implementada

**Versão**: 1.0.0

**Input**: User description: "Unidade 004 — Gerador e avaliador de senhas. Escopo: RF-14, RF-15; RN-10, RN-11. Dois endpoints públicos, sem acesso a dados de usuário: gerar senhas aleatórias e avaliar a força de uma senha."

> **Fontes normativas.** [docs/02](../../docs/02-requisitos.md) (RF-14, RF-15, RN-10, RN-11), [docs/03](../../docs/03-arquitetura.md) (endpoints e aleatoriedade injetável), [docs/04](../../docs/04-seguranca.md) §5 e [docs/07](../../docs/07-estrategia-de-testes.md) §4. O contrato está em [contracts/api.md](contracts/api.md). A unidade não depende de 002 nem de 003.

## Clarifications

### Session 2026-10-03

- Gerador e avaliador são **públicos** (confirmado pelo mantenedor na sessão de 2026-09-30).
- **O avaliador é uma heurística própria, sem dependência nova** (princípio V). Bibliotecas como `zxcvbn` dariam estimativas melhores, mas acrescentariam uma dependência e uma lista grande de dicionários para um requisito *Should*. O algoritmo fica fixado em FR-007 a FR-010 para ser determinístico e testável; trocá-lo por uma biblioteca exigiria nova versão da spec.
- A senha avaliada **nunca** é devolvida, registrada em log nem aparece em `repr` (campo `SecretStr`). A senha gerada só aparece no corpo da resposta (RNF-04).
- A resposta do avaliador traz `score` (0 a 4), `weak` (`score <= 2`, RN-11), `crack_time_seconds`, `crack_time_display` (pt-BR) e `suggestions` (pt-BR).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar uma senha (Priority: P1)

**Independent Test**: `uv run pytest tests/unit/test_password_generator.py tests/api/test_password_generator.py`

1. **Given** nenhum parâmetro, **When** `POST /api/v1/passwords/generate` com `{}`, **Then** 200 com uma senha de 20 caracteres com ao menos um caractere de cada um dos quatro conjuntos.
2. **Given** `length` e conjuntos escolhidos, **Then** a senha tem exatamente esse comprimento e usa só os conjuntos escolhidos, com ao menos um caractere de cada.
3. **Given** `exclude_ambiguous`, **Then** nenhum caractere de `0 O o 1 l I |` aparece.
4. **Given** comprimento fora de 8–128 ou nenhum conjunto, **Then** 422 `VALIDATION_ERROR`.

### User Story 2 - Avaliar a força de uma senha (Priority: P2)

**Independent Test**: `uv run pytest tests/unit/test_strength_estimator.py tests/api/test_password_strength.py`

1. **Given** uma senha de 1 a 1024 caracteres, **When** `POST /api/v1/passwords/strength`, **Then** 200 com `score`, `weak`, tempo de quebra e sugestões.
2. **Given** uma senha comum, uma sequência ou muito curta, **Then** a pontuação é baixa e as sugestões a explicam.
3. **Given** vazia ou com mais de 1024 caracteres, **Then** 422.

## Edge Cases

Todos os casos da unidade 004 em [docs/07 §4](../../docs/07-estrategia-de-testes.md): comprimento 7, 8, 128 e 129; todos os conjuntos desativados; comprimento 8 com os quatro conjuntos e `exclude_ambiguous` (um caractere de cada conjunto e nenhum ambíguo); 1.000 gerações com `exclude_ambiguous` sem ambíguos; 1.000 gerações com todo conjunto selecionado presente em cada senha; senha a avaliar com 0, 1, 1024 e 1025 caracteres.

Acrescentados por esta spec: duas gerações seguidas diferem; a distribuição de caracteres usa a fonte injetada (teste unitário com fonte determinística); a senha avaliada não aparece na resposta, nos logs nem no `repr`; a senha gerada não aparece nos logs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `POST /api/v1/passwords/generate`, público, DEVE aceitar `length` (inteiro de 8 a 128, padrão 20), `lowercase`, `uppercase`, `digits`, `symbols` (booleanos, padrão `true`) e `exclude_ambiguous` (booleano, padrão `false`), e responder 200 com `{"password": "..."}` (RF-14, RN-10).
- **FR-002**: Pelo menos um conjunto DEVE estar selecionado; violação → 422 `VALIDATION_ERROR` (RN-10).
- **FR-003**: A senha DEVE ter exatamente `length` caracteres e conter **ao menos um caractere de cada conjunto selecionado**, e somente de conjuntos selecionados (RN-10).
- **FR-004**: Os conjuntos DEVEM ser `lowercase` = `a–z`, `uppercase` = `A–Z`, `digits` = `0–9` e `symbols` = `!@#$%^&*()-_=+[]{}|;:,.<>?/~`. Com `exclude_ambiguous`, os caracteres `0 O o 1 l I |` DEVEM ser removidos de todos os conjuntos antes do sorteio (RN-10).
- **FR-005**: Toda a aleatoriedade DEVE vir de `secrets` (`randbelow`), nunca de `random`; a fonte é injetável no gerador, para teste unitário, e a ordem final dos caracteres DEVE ser embaralhada por Fisher-Yates com a mesma fonte (RNF-05, docs/03 §5).
- **FR-006**: `POST /api/v1/passwords/strength`, público, DEVE aceitar `{"password": str}` com 1 a 1024 caracteres (422 fora disso) e responder 200 com `score` (0 a 4), `weak` (`true` quando `score <= 2`), `crack_time_seconds`, `crack_time_display` e `suggestions` (RF-15, RN-11).
- **FR-007**: A entropia estimada, em bits, DEVE ser: `distintos × log2(tamanho_do_conjunto) + repetidos × 1`, em que `distintos` é o número de caracteres diferentes, `repetidos` é `len − distintos` e o tamanho do conjunto soma 26 se há minúsculas, 26 se há maiúsculas, 10 se há dígitos, 33 se há símbolos ASCII e 100 se há caracteres não ASCII. Se a senha, em minúsculas, está na lista de senhas comuns do código, a entropia é 5 bits; se é uma sequência (3 ou mais caracteres seguidos em passo +1 ou −1 de código), é `len` bits (RN-11).
- **FR-008**: A pontuação DEVE ser 0 abaixo de 28 bits, 1 abaixo de 36, 2 abaixo de 60, 3 abaixo de 80 e 4 a partir de 80 (RN-11).
- **FR-009**: O tempo de quebra DEVE ser `2^bits / (2 × 10^10)` segundos (ataque offline rápido, média de metade do espaço); `crack_time_display` DEVE ser "instantaneamente" abaixo de 1 s, depois segundos, minutos, horas, dias e anos, e "séculos" a partir de 100 anos.
- **FR-010**: As sugestões, em pt-BR, DEVEM ser: menos de 12 caracteres → "Use pelo menos 12 caracteres."; sem minúscula ou sem maiúscula → "Misture letras maiúsculas e minúsculas."; sem dígito → "Inclua números."; sem símbolo → "Inclua símbolos."; mais de 30% de caracteres repetidos → "Evite caracteres repetidos."; senha comum → "Essa senha é muito comum."; sequência → "Evite sequências como abc ou 123.". Lista vazia quando nenhuma se aplica.
- **FR-011**: A senha avaliada e a senha gerada NUNCA DEVEM ser registradas em log; a avaliada também não aparece em respostas nem em `repr` (RNF-04, docs/04 §5).

## Success Criteria *(mandatory)*

- **SC-001**: Os dois endpoints funcionam sem autenticação, e 1.000 gerações cumprem RN-10 em 100% dos casos.
- **SC-002**: 100% dos casos de borda acima têm teste `req`; RF-14, RF-15, RN-10 e RN-11 aparecem em `reports/rastreabilidade.md`.
- **SC-003**: Suíte verde, cobertura ≥ 85%, `ruff` limpo e CI verde.

## Assumptions

- Os endpoints não têm limite de taxa: são baratos e não tocam dados (risco aceito, docs/04).
- A lista de senhas comuns é pequena e fixa no código: o avaliador é indicativo, não um substituto de um dicionário real.
- Esta spec foi escrita sem `/speckit-clarify` e `/speckit-analyze`, por economia.

## Histórico de revisões

| Versão | Data | Mudança | Motivo | Origem |
|--------|------|---------|--------|--------|
| 1.0.0 | 2026-10-03 | Versão aprovada | — | PR de spec da unidade 004 |
| 1.0.0 | 2026-10-03 | Status alterado para Implementada; conteúdo sem mudança | Fase B concluída | PR de implementação da unidade 004 |
