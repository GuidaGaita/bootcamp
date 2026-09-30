"""``req`` marker validation and reports/rastreabilidade.md (research R14, FR-024 to FR-026)."""

import re
from datetime import UTC, datetime

import pytest

from tests.harness.catalog import load_catalog
from tests.harness.coverage_gate import is_default_selection

_ID = re.compile(r"(RF|RNF|RN)-\d{2}")
_CATALOG = pytest.StashKey[dict[str, str | None]]()
_ITEMS = pytest.StashKey[list[tuple[str, tuple[str, ...]]]]()
_OUTCOMES = pytest.StashKey[dict[str, str]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini(
        "requirements_catalog",
        "Documento com o catálogo de requisitos (RF, RNF, RN).",
        default="docs/02-requisitos.md",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[_CATALOG] = load_catalog(config.rootpath / config.getini("requirements_catalog"))
    config.stash[_OUTCOMES] = {}
    config.stash[_ITEMS] = []
    config.pluginmanager.register(_OutcomeRecorder(config), "cofre-outcome-recorder")


def _requirements(item: pytest.Item) -> list[tuple[str, ...]]:
    return [tuple(marker.args) for marker in item.iter_markers("req")]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    catalog = config.stash[_CATALOG]
    violations = []
    for item in items:
        for ids in _requirements(item):
            if not ids:
                violations.append(f"{item.nodeid}: req sem IDs")
            for requirement in ids:
                if not isinstance(requirement, str) or not _ID.fullmatch(requirement):
                    violations.append(f"{item.nodeid}: ID com formato inválido: {requirement}")
                elif requirement not in catalog:
                    violations.append(f"{item.nodeid}: ID inexistente no catálogo: {requirement}")
    if violations:
        raise pytest.UsageError("Marcadores req inválidos:\n" + "\n".join(violations))


def pytest_collection_finish(session: pytest.Session) -> None:
    session.config.stash[_ITEMS] = [
        (item.nodeid, tuple(sorted({r for ids in _requirements(item) for r in ids})))
        for item in session.items
    ]


class _OutcomeRecorder:
    """Records each test's outcome; TestReport carries no reference to the config."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        outcomes = self.config.stash[_OUTCOMES]
        current = outcomes.get(report.nodeid)
        if report.failed:
            outcomes[report.nodeid] = "failed"
        elif report.skipped and current != "failed":
            outcomes[report.nodeid] = "skipped"
        elif report.when == "call" and current is None:
            outcomes[report.nodeid] = "passed"


def _sort_key(requirement: str) -> tuple[int, int]:
    kind, number = requirement.split("-")
    return ({"RF": 0, "RNF": 1, "RN": 2}[kind], int(number))


def render_report(config: pytest.Config, now: datetime) -> str:
    catalog = config.stash[_CATALOG]
    items = config.stash[_ITEMS]
    outcomes = config.stash[_OUTCOMES]
    selection = "padrão" if is_default_selection(config) else "subconjunto"

    by_requirement: dict[str, list[str]] = {}
    for nodeid, requirements in items:
        for requirement in requirements:
            by_requirement.setdefault(requirement, []).append(nodeid)

    lines = [
        "# Rastreabilidade requisito → testes",
        "",
        f"Execução: {now:%Y-%m-%dT%H:%M:%SZ} · Seleção: {selection} · Testes: {len(items)}",
        "",
        "| Requisito | Prioridade | Testes | Resultado |",
        "|-----------|------------|--------|-----------|",
    ]
    for requirement in sorted(by_requirement, key=_sort_key):
        priority = catalog.get(requirement) or "—"
        for nodeid in sorted(by_requirement[requirement]):
            outcome = outcomes.get(nodeid, "not run")
            lines.append(f"| {requirement} | {priority} | {nodeid} | {outcome} |")

    missing = [
        requirement
        for requirement, priority in sorted(catalog.items(), key=lambda entry: _sort_key(entry[0]))
        if priority == "Must" and requirement not in by_requirement
    ]
    lines += ["", "## Requisitos Must sem teste", ""]
    lines += [f"- {requirement}" for requirement in missing] or ["Nenhum."]
    return "\n".join(lines) + "\n"


def pytest_sessionfinish(session: pytest.Session) -> None:
    config = session.config
    if _ITEMS not in config.stash:
        return
    path = config.rootpath / "reports" / "rastreabilidade.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(config, datetime.now(UTC)), encoding="utf-8")
