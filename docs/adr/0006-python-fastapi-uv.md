# ADR-0006 — Python 3.13 + FastAPI + uv

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** @GuidaGaita (linguagem); Claude Code (framework e ferramentas, por delegação)
- **Relacionados:** [Sessão grill-me Q6](../sessoes/2026-09-13-grill-me-definicao-inicial.md), [ADR-0005](0005-api-rest-multiusuario-sem-frontend.md)

## Contexto

O mantenedor escolheu Python. Falta definir o framework web e as ferramentas. O sistema precisa de validação rigorosa de entrada, contratos OpenAPI, bibliotecas criptográficas maduras e um ambiente reprodutível.

## Decisão

| Área | Escolha |
|------|---------|
| Linguagem | **Python 3.13** |
| Framework web | **FastAPI** + **Pydantic v2** (validação e schemas) + **Uvicorn** |
| Configuração | **pydantic-settings** (variáveis `COFRE_*`) |
| Criptografia | **cryptography** (AES-GCM, HKDF) e **argon2-cffi** (Argon2id) |
| Dependências e ambiente virtual | **uv** (`pyproject.toml` + `uv.lock`) |
| Lint e formatação | **ruff** (incluindo as regras `S` de segurança) |
| Testes | **pytest** ([ADR-0013](0013-harness-de-testes-com-pytest.md)) |

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Flask | Sem validação nem OpenAPI nativos; exigiria extensões. |
| Django + DRF | Pesado demais para uma API pequena, com ORM e admin desnecessários. |
| pip + `requirements.txt` | Sem lockfile confiável; instalação lenta. |
| Poetry | Funciona, mas o uv é mais rápido e já é exigido pelo Spec Kit. |

## Consequências

**Positivas**

- OpenAPI gerado automaticamente a partir dos schemas, alinhado aos contratos das specs.
- Validação declarativa das regras de formato (RN-02, RN-06, RN-10, RN-13).
- Uma única ferramenta (uv) para dependências, execução e instalação do Spec Kit.

**Negativas / riscos**

- Python não garante apagar segredos da memória (risco aceito em [04-seguranca.md](../04-seguranca.md#6-riscos-aceitos)).
- As mensagens de validação padrão do FastAPI precisam ser adaptadas ao formato de erro do projeto.
