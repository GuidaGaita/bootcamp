"""Coverage gate only on the full default selection (research R14, FR-027)."""

import pytest

DEFAULT_MARKEXPR = "not perf and not smoke"


def is_default_selection(config: pytest.Config) -> bool:
    return (
        config.option.markexpr == DEFAULT_MARKEXPR
        and not config.option.keyword
        and config.args_source == pytest.Config.ArgsSource.TESTPATHS
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    if is_default_selection(config):
        return
    config.option.cov_fail_under = 0
    # pytest-cov keeps its own namespace, created before the command line is fully parsed.
    cov_plugin = config.pluginmanager.get_plugin("_cov")
    if cov_plugin is not None:
        cov_plugin.options.cov_fail_under = 0
