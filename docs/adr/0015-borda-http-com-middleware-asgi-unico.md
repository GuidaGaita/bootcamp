# ADR-0015 — Borda HTTP com middleware ASGI único

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [spec 001](../../specs/001-fundacao-da-api/spec.md), [research R4, R10–R12](../../specs/001-fundacao-da-api/research.md), RNF-04, RNF-08, RNF-13, RNF-14, [03-arquitetura.md §5–6](../03-arquitetura.md)

## Contexto

Toda resposta da API precisa sair com `X-Request-ID` validado, as de `/api/v1` também com `Cache-Control: no-store`, e cada requisição gera uma linha de log JSON sem dados sensíveis. Erros inesperados devem virar 500 no formato padronizado.

No Starlette, que é a base do FastAPI, o handler de `Exception` roda no `ServerErrorMiddleware`, **fora** dos middlewares de usuário. Por isso, um 500 tratado ali sai sem os cabeçalhos transversais e sem passar pelo log da requisição. O `BaseHTTPMiddleware` (`@app.middleware("http")`) tem limitações conhecidas com respostas em *streaming* e *background tasks*. O log de acesso do Uvicorn registra o caminho com *query string* e não é JSON.

## Decisão

- Um único middleware **ASGI puro**, `RequestContextMiddleware`, registrado como o mais externo entre os de usuário, concentra a borda HTTP. Ele:
  - define o `request_id`;
  - acrescenta os cabeçalhos transversais;
  - mede a duração;
  - converte exceções não tratadas em 500 `INTERNAL_ERROR`;
  - emite o log da requisição e o log de erro.
- Os demais erros (404, 405, 422 e erros de domínio) são traduzidos por *exception handlers* do FastAPI a partir de um catálogo único `code → status/mensagem`.
- Logs usam o módulo `logging` da biblioteca padrão, com um formatador JSON próprio, sem registrar corpo, *query string*, valores de cabeçalhos nem a mensagem da exceção. A decisão de emitir usa o nível configurado da aplicação.
- O Uvicorn roda com `--no-access-log`.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Handler de `Exception` para o 500 | A resposta sai sem `X-Request-ID`/`Cache-Control` e fora do log da requisição. |
| `BaseHTTPMiddleware` | Problemas com *streaming* e *background tasks*; o ganho de ergonomia não compensa. |
| Vários middlewares pequenos | A ordem entre eles vira um contrato implícito e frágil. |
| `structlog` ou `python-json-logger` | Dependência a mais para uma linha JSON por requisição (princípio V). |
| Manter o log de acesso do Uvicorn | Registra *query string* e não é estruturado (RNF-04, RNF-13). |

## Consequências

**Positivas**

- Nenhuma resposta, inclusive de erro, escapa sem cabeçalhos transversais e sem log.
- A higiene de logs fica num ponto só, fácil de testar (captura de logs com valores marcadores).
- As unidades seguintes só acrescentam códigos ao catálogo de erros.

**Negativas / riscos**

- Um middleware ASGI puro é mais verboso que `BaseHTTPMiddleware` e exige cuidado ao interceptar `http.response.start`.
- Sem a mensagem da exceção, o diagnóstico depende do tipo e da pilha; o `request_id` ajuda a reproduzir o caso.
