import pytest

from tests.support.harness_project import build_project

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-09")]

NO_COV = ("--no-cov", "-p", "no:cacheprovider")


def _run(pytester, monkeypatch, source, *args):
    build_project(pytester, monkeypatch, source)
    return pytester.runpytest_subprocess(*NO_COV, *args)


def _report(pytester) -> str:
    return (pytester.path / "reports" / "rastreabilidade.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("bad_id", ["RF-1", "RF-99"])
def test_invalid_or_unknown_requirement_fails_citing_test_and_id(pytester, monkeypatch, bad_id):
    source = f"""
import pytest

@pytest.mark.req("{bad_id}")
def test_bad():
    pass
"""
    result = _run(pytester, monkeypatch, source)

    assert result.ret != 0
    output = result.stdout.str() + result.stderr.str()
    assert "test_sample.py::test_bad" in output
    assert bad_id in output


def test_req_without_ids_fails(pytester, monkeypatch):
    source = """
import pytest

@pytest.mark.req()
def test_empty():
    pass
"""
    result = _run(pytester, monkeypatch, source)

    assert result.ret != 0
    assert "test_sample.py::test_empty" in result.stdout.str() + result.stderr.str()


def test_unregistered_marker_fails(pytester, monkeypatch):
    source = """
import pytest

@pytest.mark.not_registered
def test_marker():
    pass
"""
    result = _run(pytester, monkeypatch, source)

    assert result.ret != 0


def test_report_lists_tests_per_requirement_and_must_without_test(pytester, monkeypatch):
    source = """
import pytest

@pytest.mark.req("RF-01")
def test_first():
    pass
"""
    result = _run(pytester, monkeypatch, source)

    assert result.ret == 0
    report = _report(pytester)
    assert "Seleção: padrão" in report
    assert "| RF-01 | Must | suite/test_sample.py::test_first | passed |" in report
    must_section = report.split("## Requisitos Must sem teste", 1)[1]
    assert "RF-02" in must_section
    assert "RF-01" not in must_section
    assert "RF-03" not in must_section


def test_report_is_written_even_when_a_test_fails(pytester, monkeypatch):
    source = """
import pytest

@pytest.mark.req("RF-01", "RNF-12")
def test_failing():
    assert False
"""
    result = _run(pytester, monkeypatch, source)

    assert result.ret == 1
    report = _report(pytester)
    assert "| RF-01 | Must | suite/test_sample.py::test_failing | failed |" in report
    assert "| RNF-12 | Should | suite/test_sample.py::test_failing | failed |" in report


def test_report_marks_subset_selection(pytester, monkeypatch):
    source = """
import pytest

@pytest.mark.unit
@pytest.mark.req("RF-01")
def test_first():
    pass
"""
    result = _run(pytester, monkeypatch, source, "-m", "unit")

    assert result.ret == 0
    assert "Seleção: subconjunto" in _report(pytester)
