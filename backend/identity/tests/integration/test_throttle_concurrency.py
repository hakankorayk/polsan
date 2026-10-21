"""R-05 reproduction for review finding N1: concurrent failed logins on two usernames whose
throttle rows are both stale must not deadlock in ``_purge_stale``.

Interleaving forced from the test side only: ``_purge_stale`` is wrapped so that each thread waits
on a barrier until BOTH transactions have locked and updated their own row, then both purge. If
the purge DELETE tries to lock the other transaction's (old, stale) row version, PostgreSQL
detects a deadlock and aborts one of them.
"""

import threading
from datetime import datetime, timedelta

import pytest
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone

from identity import services
from identity.models import LoginThrottle

USERNAMES = ("stale-a", "stale-b")
WRONG_PASSWORD = "yanlis-parola-123"
BARRIER_TIMEOUT = 10  # seconds; only reached if one thread never gets to the purge
JOIN_TIMEOUT = 30  # seconds; a thread still alive after this is a hang, reported as such


@pytest.mark.django_db(transaction=True)
def test_concurrent_failures_on_two_stale_rows_do_not_deadlock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale = timezone.now() - timedelta(minutes=20)
    for username in USERNAMES:
        LoginThrottle.objects.create(
            username=username, failures=[stale.isoformat()], locked_until=None, updated_at=stale
        )

    barrier = threading.Barrier(2, timeout=BARRIER_TIMEOUT)
    barrier_problems: list[str] = []
    original_purge = services._purge_stale

    def purge_after_both_locked(now: datetime) -> None:
        try:
            barrier.wait()
        except threading.BrokenBarrierError:
            # The other thread never reached its purge: record it, still purge so we never hang.
            barrier_problems.append(f"{threading.current_thread().name}: barrier broken")
        original_purge(now)

    monkeypatch.setattr(services, "_purge_stale", purge_after_both_locked)

    outcomes: dict[str, BaseException | None] = {}
    started = timezone.now()

    def attempt(username: str) -> None:
        try:
            services.log_in(RequestFactory().post("/api/auth/login/"), username, WRONG_PASSWORD)
            outcomes[username] = None  # a success would itself be wrong; flagged below
        except BaseException as exc:  # noqa: BLE001 — the test must see every outcome
            outcomes[username] = exc
            if not isinstance(exc, services.InvalidCredentialsError):
                barrier.abort()  # do not let the other thread wait out the barrier timeout
        finally:
            connection.close()

    threads = [
        threading.Thread(target=attempt, args=(username,), name=username) for username in USERNAMES
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(JOIN_TIMEOUT)

    hung = [thread.name for thread in threads if thread.is_alive()]
    assert not hung, f"threads still running after {JOIN_TIMEOUT}s (hang): {hung}"
    unexpected = {
        username: repr(exc)
        for username, exc in outcomes.items()
        if not isinstance(exc, services.InvalidCredentialsError)
    }
    assert set(outcomes) == set(USERNAMES), f"missing outcomes: {outcomes}"
    assert not unexpected, f"expected InvalidCredentialsError for both, got: {unexpected}"
    assert not barrier_problems, f"forced interleaving did not happen: {barrier_problems}"

    for username in USERNAMES:
        row = LoginThrottle.objects.filter(username=username).first()
        assert row is not None, f"{username}: throttle row lost, the failure was not recorded"
        latest = max(datetime.fromisoformat(t) for t in row.failures)
        assert latest >= started, f"{username}: no fresh failure recorded ({row.failures})"
        assert row.updated_at >= started, f"{username}: row not updated ({row.updated_at})"
