# ADR-0014 — Ambiente reprodutível com Docker Compose e GitHub Actions

- **Status:** Aceita
- **Data:** 2026-09-13
- **Decisores:** Claude Code, por delegação de @GuidaGaita
- **Relacionados:** [08-ambiente-e-agentes.md](../08-ambiente-e-agentes.md), RNF-10, RNF-15

## Contexto

O desenvolvimento acontece no Windows, enquanto a aplicação e o CI rodam em Linux. A entrega exige arquivos de padronização do ambiente que garantam reprodutibilidade, e o harness precisa rodar da mesma forma na máquina do mantenedor, na de um avaliador e no CI.

## Decisão

- **`Dockerfile`** multi-stage baseado em `python:3.13-slim`, com dependências instaladas por `uv sync --frozen` e execução como usuário não-root.
- **`docker-compose.yml`** com dois serviços:
  - `api`: Uvicorn na porta 8000 e volume `cofre-data` para o SQLite;
  - `tests`: executa a suíte completa e grava os artefatos em `./reports`.
- **`uv.lock`** versionado, para as mesmas versões de dependências em todos os ambientes.
- **`.gitattributes`** com `eol=lf`, evitando problemas de fim de linha entre Windows e Linux.
- **GitHub Actions** (`ci.yml`): `lint` → `test` (com gate de cobertura e upload de `reports/`) → `docker` (build da imagem), em PRs e pushes para `develop` e `main`.
- `.gitattributes` e esta decisão entram no incremento 0; os demais arquivos, no incremento 1.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| Apenas `uv` local, sem Docker | Reprodutível para dependências Python, mas não para o sistema operacional e o runtime de produção. |
| Dev Containers | Bom para desenvolvimento, mas não substitui o compose para execução e testes por terceiros. |
| `Makefile` | Atrito no Windows; os comandos `docker compose` e `uv run` já são curtos. |

## Consequências

**Positivas**

- `docker compose up` e `docker compose run --rm tests` funcionam iguais em qualquer máquina com Docker.
- O CI reproduz exatamente o ambiente de testes.

**Negativas / riscos**

- O primeiro build é mais lento; mitigado pelo cache de camadas e pela velocidade do uv.
- Exige Docker instalado para o caminho recomendado; o caminho alternativo com `uv` fica documentado.
