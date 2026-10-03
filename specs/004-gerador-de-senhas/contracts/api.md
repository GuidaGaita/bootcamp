# Contrato: Gerador e avaliador de senhas

Erros e convenções em [docs/03 §6](../../../docs/03-arquitetura.md). Os dois endpoints são públicos. Toda resposta de `/api/v1` leva `Cache-Control: no-store` e `X-Request-ID`.

| Rota | Corpo | Sucesso | Erros |
|------|-------|---------|-------|
| `POST /api/v1/passwords/generate` | `{length?: int 8–128 (20), lowercase?: bool (true), uppercase?: bool (true), digits?: bool (true), symbols?: bool (true), exclude_ambiguous?: bool (false)}` | 200 `{password: str}` | 422 |
| `POST /api/v1/passwords/strength` | `{password: str}` (1–1024 caracteres) | 200 `{score: int 0–4, weak: bool, crack_time_seconds: float, crack_time_display: str, suggestions: [str]}` | 422 |

Notas:

- `weak` é `true` quando `score <= 2` (RN-11).
- `crack_time_seconds` é um número finito; para entropias muito altas é limitado a `1e300`, para a resposta continuar sendo um JSON válido.
- 422 quando nenhum conjunto de caracteres é selecionado: `details` traz `field` = `body`.
