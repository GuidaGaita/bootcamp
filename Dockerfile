# Imagem multi-stage do Cofre (research R15, ADR-0014).
#   runtime: API sem dependências de desenvolvimento, usuário sem privilégios.
#   test:    suíte completa; usado por `docker compose run --rm tests`.

FROM python:3.13-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS build
# Camada de dependências, reaproveitada enquanto o lock não muda.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime
RUN groupadd --system --gid 10001 cofre \
    && useradd --system --uid 10001 --gid cofre --no-create-home cofre \
    && mkdir /data \
    && chown cofre:cofre /data
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER cofre
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status != 200)"]
CMD ["uvicorn", "cofre.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM build AS test
RUN uv sync --frozen
COPY tests/ tests/
COPY specs/ specs/
COPY docs/02-requisitos.md docs/02-requisitos.md
COPY .github/workflows/ .github/workflows/
ENV PATH="/app/.venv/bin:$PATH"
CMD ["pytest"]
