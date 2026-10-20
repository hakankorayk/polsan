"""Spec 0002 — AC-8, AC-9, AC-27: five failures in 15 minutes lock for 15 minutes."""

from datetime import UTC, datetime, timedelta

from identity.domain.throttle import (
    ThrottleState,
    is_locked,
    register_failure,
    register_success,
)

T0 = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)


def _fail(times: int, start: ThrottleState | None = None, step=timedelta(seconds=10)):
    state = start or ThrottleState()
    now = T0
    for _ in range(times):
        state = register_failure(state, now)
        now += step
    return state, now


def test_four_failures_do_not_lock() -> None:
    state, now = _fail(4)

    assert not is_locked(state, now)


def test_fifth_failure_locks_for_15_minutes() -> None:
    state, now = _fail(5)
    fifth = now - timedelta(seconds=10)

    assert is_locked(state, fifth)
    assert is_locked(state, fifth + timedelta(minutes=14, seconds=59))


def test_lock_expires() -> None:
    state, now = _fail(5)
    fifth = now - timedelta(seconds=10)

    assert not is_locked(state, fifth + timedelta(minutes=15))


def test_failures_during_lock_do_not_extend_it() -> None:
    state, now = _fail(5)
    locked_until = state.locked_until

    state = register_failure(state, now + timedelta(minutes=10))

    assert state.locked_until == locked_until


def test_unknown_username_locks_the_same() -> None:
    # The throttle keys on the username string only; existence is never consulted.
    state, now = _fail(5)

    assert is_locked(state, now)


def test_old_failures_outside_window_not_counted() -> None:
    state, _ = _fail(4)
    later = T0 + timedelta(minutes=16)

    state = register_failure(state, later)

    assert not is_locked(state, later)
    assert len(state.failures) == 1


def test_success_resets_counter() -> None:
    state, now = _fail(4)
    state = register_success()
    state, now = _fail(4, start=state)

    assert not is_locked(state, now)
