# Implementation Plan: Gerador e avaliador de senhas

**Branch**: `spec/004-gerador-de-senhas` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md) | **Contrato**: [contracts/api.md](contracts/api.md)

## Summary

Duas funções puras (gerar e avaliar) atrás de dois endpoints públicos. Sem dependências novas, sem persistência.

**Constitution Check**: I ✅ · II ✅ (`secrets`, nada em log, `SecretStr`) · III ✅ testes primeiro, fonte aleatória injetável, 1.000 gerações nos testes · IV ✅ contrato em `contracts/api.md`; `services` sem FastAPI · V ✅ heurística própria em vez de dependência (ver *Clarifications*).

## Project Structure

```text
src/cofre/
├── services/passwords.py        PasswordGenerator (rng injetável) · StrengthEstimator · StrengthResult
└── api/
    ├── schemas/passwords.py     GenerateRequest/Response · StrengthRequest/Response
    └── routers/passwords.py     POST /generate · POST /strength (sem autenticação)
tests/
├── unit/test_password_generator.py · test_strength_estimator.py
└── api/test_password_generator.py · test_password_strength.py · security/test_password_hygiene.py
```

## Decisões de implementação

- **Fonte aleatória:** `PasswordGenerator(randbelow=secrets.randbelow)`; os testes injetam uma fonte determinística. O embaralhamento é Fisher-Yates com a mesma fonte (o módulo `random` é proibido).
- **Sorteio com garantia de conjunto:** um caractere de cada conjunto selecionado, o restante do conjunto união, e depois o embaralhamento.
- **Validação cruzada** (nenhum conjunto) num `model_validator` do esquema; o limite de comprimento, em `Field(ge=8, le=128)`.
- **Estimador** puro e determinístico: entropia, pontuação, tempo e sugestões conforme FR-007 a FR-010; `crack_time_seconds` limitado a `1e300`.
