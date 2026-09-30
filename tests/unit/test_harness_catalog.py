import pytest

from tests.harness.catalog import load_catalog
from tests.support.harness_project import REPO_ROOT, SAMPLE_CATALOG

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-09")]


def test_reads_ids_and_priorities_from_table_rows(tmp_path):
    path = tmp_path / "catalog.md"
    path.write_text(SAMPLE_CATALOG, encoding="utf-8")

    assert load_catalog(path) == {
        "RF-01": "Must",
        "RF-02": "Must",
        "RF-03": "Could",
        "RNF-12": "Should",
        "RN-01": None,
    }


def test_reads_real_requirements_document():
    catalog = load_catalog(REPO_ROOT / "docs" / "02-requisitos.md")

    expected = (
        {f"RF-{n:02d}" for n in range(1, 17)}
        | {f"RNF-{n:02d}" for n in range(1, 16)}
        | {f"RN-{n:02d}" for n in range(1, 17)}
    )
    assert expected <= set(catalog)
    assert catalog["RF-01"] == "Must"
    assert catalog["RN-01"] is None
