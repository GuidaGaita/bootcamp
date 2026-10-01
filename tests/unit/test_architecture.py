"""Layer dependency rule (docs/03 §2.2, constitution principle IV)."""

import ast
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-11")]

SRC = Path(__file__).resolve().parents[2] / "src" / "cofre"

FORBIDDEN: dict[str, set[str]] = {
    "core": {"cofre.api", "cofre.services", "cofre.repositories", "cofre.crypto", "cofre.main"},
    "crypto": {"cofre.api", "cofre.services", "cofre.repositories", "cofre.core", "cofre.main"},
    "repositories": {"cofre.services", "cofre.api", "cofre.main"},
    "services": {"cofre.api", "cofre.main", "fastapi", "starlette"},
}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def _violations(layer: str) -> list[str]:
    found = []
    for path in sorted((SRC / layer).rglob("*.py")):
        for module in _imported_modules(path):
            for forbidden in FORBIDDEN[layer]:
                if module == forbidden or module.startswith(forbidden + "."):
                    found.append(f"{path.relative_to(SRC)} importa {module}")
    return found


@pytest.mark.parametrize("layer", sorted(FORBIDDEN))
def test_layer_does_not_import_upper_layers(layer):
    assert (SRC / layer).is_dir()
    assert _violations(layer) == []


def test_detects_forbidden_import(tmp_path):
    module = tmp_path / "bad.py"
    module.write_text("from fastapi import FastAPI\nimport cofre.api.deps\n", encoding="utf-8")

    assert _imported_modules(module) == {"fastapi", "cofre.api.deps"}
