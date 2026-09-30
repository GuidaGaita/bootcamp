"""Structure of .github/workflows/ci.yml (research R16, R21)."""

from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.unit, pytest.mark.req("RNF-10", "RNF-11")]

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    # PyYAML (YAML 1.1) reads the bare key "on" as the boolean True.
    return workflow.get("on", workflow.get(True))


def _run_lines(job: dict) -> str:
    return "\n".join(step.get("run", "") for step in job["steps"])


@pytest.mark.parametrize("event", ["pull_request", "push"])
def test_triggers_on_develop_and_main(workflow, event):
    assert set(_triggers(workflow)[event]["branches"]) == {"develop", "main"}


def test_jobs_are_chained_lint_test_docker(workflow):
    jobs = workflow["jobs"]

    assert set(jobs) >= {"lint", "test", "docker"}
    assert "needs" not in jobs["lint"]
    assert jobs["test"]["needs"] in ("lint", ["lint"])
    assert jobs["docker"]["needs"] in ("test", ["test"])


@pytest.mark.parametrize(
    ("job", "command"),
    [
        ("lint", "uv lock --check"),
        ("lint", "ruff check"),
        ("lint", "ruff format --check"),
        ("test", "pytest"),
        ("docker", "pytest -m smoke"),
        ("docker", "docker compose run --rm tests"),
    ],
)
def test_job_runs_required_command(workflow, job, command):
    assert command in _run_lines(workflow["jobs"][job])


def test_reports_are_uploaded_even_on_failure(workflow):
    uploads = [
        step
        for step in workflow["jobs"]["test"]["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact")
    ]

    assert uploads
    assert uploads[0]["if"] == "always()"
    assert "reports" in uploads[0]["with"]["path"]


def test_permissions_are_read_only(workflow):
    assert workflow["permissions"] == {"contents": "read"}
