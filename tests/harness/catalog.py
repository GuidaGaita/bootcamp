"""Requirement catalog read from docs/02-requisitos.md (research R14)."""

import re
from pathlib import Path

_ROW = re.compile(r"^\|\s*((?:RF|RNF|RN)-\d{2})\s*\|(.*)$")
PRIORITIES = ("Must", "Should", "Could", "Won't")


def load_catalog(path: Path) -> dict[str, str | None]:
    """Map each requirement ID to its priority (``None`` for business rules)."""
    catalog: dict[str, str | None] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = _ROW.match(line.strip())
        if not match:
            continue
        requirement, rest = match.groups()
        cells = [cell.strip() for cell in rest.split("|")]
        priority = next((cell for cell in cells if cell in PRIORITIES), None)
        if catalog.get(requirement) is None:
            catalog[requirement] = priority
    return catalog
