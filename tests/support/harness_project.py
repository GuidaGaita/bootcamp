"""Synthetic project used by the harness self-tests (tests/unit/test_harness_*.py)."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_CATALOG = """\
# Catálogo de exemplo

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-01 | Primeiro requisito | Must |
| RF-02 | Segundo requisito, ainda sem teste | Must |
| RF-03 | Requisito opcional | Could |

| ID | Categoria | Requisito | Prioridade | Verificação |
|----|-----------|-----------|------------|-------------|
| RNF-12 | Desempenho | Rápido | Should | Testes perf |

| ID | Regra | Relacionado |
|----|-------|-------------|
| RN-01 | Regra de negócio | RF-01 |

RF-04 aparece fora de tabela e deve ser ignorado.

| RF-01 | 001 | spec | — | Especificado |
"""

PYPROJECT = """\
[tool.pytest.ini_options]
testpaths = ["suite"]
pythonpath = ["."]
requirements_catalog = "catalog.md"
markers = [
    "unit: unit",
    "integration: integration",
    "api: api",
    "security: security",
    "perf: perf",
    "smoke: smoke",
    "req(*ids): requirements",
]
addopts = [
    "-p", "tests.harness.plugin",
    "-p", "no:randomly",
    "--strict-markers",
    "-m", "not perf and not smoke",
    "--cov=samplepkg",
    "--cov-branch",
    "--cov-fail-under=85",
    "--cov-report=term-missing",
    "--cov-report=xml:reports/coverage.xml",
    "--cov-report=html:reports/htmlcov",
    "--junitxml=reports/junit.xml",
]
"""

SAMPLE_PACKAGE = """\
def covered(value: int) -> int:
    return value + 1


def uncovered(value: int) -> int:
    if value > 10:
        return value * 2
    if value < 0:
        return -value
    for item in range(value):
        value += item
    return value
"""


def build_project(pytester, monkeypatch, test_source: str) -> None:
    """Write the synthetic project into ``pytester.path`` with ``test_source`` as its suite."""
    monkeypatch.setenv("PYTHONPATH", str(REPO_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    monkeypatch.setenv("PYTHONUTF8", "1")
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    pytester.makefile(".toml", pyproject=PYPROJECT)
    pytester.makefile(".md", catalog=SAMPLE_CATALOG)
    package = pytester.mkpydir("samplepkg")
    (package / "__init__.py").write_text(SAMPLE_PACKAGE, encoding="utf-8")
    suite = pytester.mkdir("suite")
    (suite / "test_sample.py").write_text(test_source, encoding="utf-8")
