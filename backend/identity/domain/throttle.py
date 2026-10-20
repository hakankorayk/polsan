"""Login throttle per username (spec 0002, AC-8, AC-9, AC-27; ADR 0003). Pure Python.

Five failures within the last 15 minutes lock the username for 15 minutes. A success clears the
counter. Unknown usernames are throttled exactly like real ones, so a lock reveals nothing.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

MAX_FAILURES = 5
WINDOW = timedelta(minutes=15)
LOCK_DURATION = timedelta(minutes=15)


@dataclass(frozen=True)
class ThrottleState:
    failures: tuple[datetime, ...] = ()
    locked_until: datetime | None = None


def is_locked(state: ThrottleState, now: datetime) -> bool:
    return state.locked_until is not None and now < state.locked_until


def register_failure(state: ThrottleState, now: datetime) -> ThrottleState:
    if is_locked(state, now):
        return state  # attempts during a lock neither count nor extend it
    recent = tuple(t for t in state.failures if now - t < WINDOW) + (now,)
    if len(recent) >= MAX_FAILURES:
        return ThrottleState(failures=(), locked_until=now + LOCK_DURATION)
    return ThrottleState(failures=recent, locked_until=None)


def register_success() -> ThrottleState:
    return ThrottleState()
