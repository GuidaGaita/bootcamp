from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from cofre.core.errors import TooManyAttemptsError
from cofre.crypto import hashing
from cofre.main import create_app
from cofre.services.throttle import ThrottleService
from tests.conftest import make_settings
from tests.support.auth import login, register
from tests.support.clock import FakeClock

pytestmark = [pytest.mark.integration, pytest.mark.req("RN-14", "RN-16", "RNF-07")]


@pytest.fixture
def service(client, app, clock, settings):
    session = app.state.session_factory()
    yield ThrottleService(session, clock, settings)
    session.close()


def test_sixth_attempt_is_refused_even_if_earlier_ones_never_finished(service):
    # Attempts are counted before verification: a burst of in-flight guesses cannot exceed 5.
    for expected in range(1, 6):
        assert service.begin_attempt("ana@email.com") == expected

    with pytest.raises(TooManyAttemptsError) as raised:
        service.begin_attempt("ana@email.com")

    assert raised.value.headers["Retry-After"] == "900"


def test_register_failure_locks_only_when_the_limit_is_reached(service):
    assert service.register_failure("ana@email.com", 4) is False
    assert service.register_failure("ana@email.com", 5) is True


def test_expired_lock_starts_a_fresh_count(service, clock):
    for _ in range(5):
        service.begin_attempt("ana@email.com")
    service.register_failure("ana@email.com", 5)
    clock.advance(minutes=15)

    assert service.begin_attempt("ana@email.com") == 1


def test_idle_rows_are_pruned_so_unknown_emails_do_not_accumulate(service, clock, app):
    for index in range(20):
        service.begin_attempt(f"ninguem{index}@email.com")
    clock.advance(hours=25)

    service.begin_attempt("outro@email.com")

    with app.state.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM login_throttles")).scalar_one() == 1


def test_locked_rows_are_kept_until_the_lock_ends(service, clock, app):
    for _ in range(5):
        service.begin_attempt("ana@email.com")
    service.register_failure("ana@email.com", 5)
    clock.advance(minutes=14, seconds=59)

    with pytest.raises(TooManyAttemptsError):
        service.begin_attempt("ana@email.com")


def test_parallel_wrong_logins_admit_at_most_five_guesses(tmp_path):
    app = create_app(make_settings(tmp_path), FakeClock())
    with TestClient(app) as client:
        assert register(client, "ana@email.com").status_code == 201

        def guess(_: int) -> int:
            return login(client, "ana@email.com", "senha-errada-qualquer").status_code

        with ThreadPoolExecutor(max_workers=12) as pool:
            statuses = list(pool.map(guess, range(24)))

    assert statuses.count(401) <= 5
    assert statuses.count(401) + statuses.count(429) == 24


def test_dummy_hash_is_built_when_the_app_is_created(tmp_path):
    settings = make_settings(tmp_path, argon2_memory_kib=1536)
    hashing.dummy_hash.cache_clear()

    create_app(settings, FakeClock())

    assert hashing.dummy_hash.cache_info().currsize == 1


def test_argon2_cost_is_exposed_in_crypto_argument_order(settings):
    assert settings.argon2_cost == (1024, 1, 1)
