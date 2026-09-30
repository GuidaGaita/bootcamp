"""Test harness plugin: traceability, coverage gate and output log (RNF-09, research R14)."""

pytest_plugins = [
    "tests.harness.coverage_gate",
    "tests.harness.output_log",
    "tests.harness.traceability",
]
