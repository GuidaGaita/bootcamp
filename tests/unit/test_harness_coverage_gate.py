import pytest

from tests.support.harness_project import build_project

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-09")]

PASSING_LOW_COVERAGE = """
import pytest

from samplepkg import covered

@pytest.mark.unit
@pytest.mark.req("RF-01")
def test_sample():
    assert covered(1) == 2
"""

FAILING = """
import pytest

@pytest.mark.unit
@pytest.mark.req("RF-01")
def test_sample():
    assert False
"""


def test_default_selection_fails_below_threshold_even_if_tests_pass(pytester, monkeypatch):
    build_project(pytester, monkeypatch, PASSING_LOW_COVERAGE)

    result = pytester.runpytest_subprocess()

    assert result.ret != 0
    result.stdout.fnmatch_lines(["*1 passed*"])
    assert "fail-under" in result.stdout.str().lower() or "fail_under" in result.stdout.str()


@pytest.mark.parametrize(
    "args",
    [("-m", "unit"), ("-k", "sample"), ("suite/test_sample.py",)],
    ids=["marker", "keyword", "path"],
)
def test_subset_selection_ignores_threshold(pytester, monkeypatch, args):
    build_project(pytester, monkeypatch, PASSING_LOW_COVERAGE)

    result = pytester.runpytest_subprocess(*args)

    assert result.ret == 0


def test_artifacts_are_written_when_a_test_fails(pytester, monkeypatch):
    build_project(pytester, monkeypatch, FAILING)

    result = pytester.runpytest_subprocess()

    assert result.ret != 0
    reports = pytester.path / "reports"
    for artifact in ("junit.xml", "coverage.xml", "htmlcov/index.html", "pytest-output.log"):
        assert (reports / artifact).is_file(), artifact
    log = (reports / "pytest-output.log").read_text(encoding="utf-8")
    assert "1 failed" in log
    assert "\x1b[" not in log


def test_log_strips_color_codes(pytester, monkeypatch):
    build_project(pytester, monkeypatch, FAILING)

    pytester.runpytest_subprocess("--color=yes", "--no-cov")

    log = (pytester.path / "reports" / "pytest-output.log").read_text(encoding="utf-8")
    assert "1 failed" in log
    assert "\x1b[" not in log
