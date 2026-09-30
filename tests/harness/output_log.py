"""Copy of the terminal output to reports/pytest-output.log (research R14, FR-028).

Same technique as pytest's own ``pastebin`` plugin: wrap the terminal writer.
"""

import re

import pytest

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_LOG_FILE = pytest.StashKey[object]()


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    reporter = config.pluginmanager.getplugin("terminalreporter")
    if reporter is None:
        return
    path = config.rootpath / "reports" / "pytest-output.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    log = path.open("w", encoding="utf-8")
    config.stash[_LOG_FILE] = log
    original_write = reporter._tw.write

    def tee_write(text: str, **markup: bool) -> None:
        original_write(text, **markup)
        log.write(_ANSI_ESCAPE.sub("", str(text)))

    reporter._tw.write = tee_write


def pytest_unconfigure(config: pytest.Config) -> None:
    log = config.stash.get(_LOG_FILE, None)
    if log is not None:
        log.close()
        del config.stash[_LOG_FILE]
