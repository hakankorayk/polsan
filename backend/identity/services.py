"""Login, logout and the forced password change (spec 0002). Views stay thin; rules live here
and in identity.domain."""

from datetime import datetime

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from employees.api import (
    active_direct_reports,
    get_employee,
    has_active_direct_reports,
    is_employee_active,
)
from identity.domain.roles import Role, derive_roles
from identity.domain.throttle import (
    LOCK_DURATION,
    WINDOW,
    ThrottleState,
    is_locked,
    register_failure,
    register_success,
)
from identity.domain.usernames import MAX_LENGTH, normalize_username
from identity.models import LoginThrottle, User


class InvalidCredentialsError(Exception):
    pass


class LoginLockedError(Exception):
    pass


def _state(row: LoginThrottle) -> ThrottleState:
    return ThrottleState(
        failures=tuple(datetime.fromisoformat(t) for t in row.failures),
        locked_until=row.locked_until,
    )


def _store(row: LoginThrottle, state: ThrottleState, now: datetime) -> None:
    row.failures = [t.isoformat() for t in state.failures]
    row.locked_until = state.locked_until
    row.updated_at = now
    row.save(update_fields=["failures", "locked_until", "updated_at"])


def _purge_stale(now: datetime) -> None:
    """Rows nobody needs any more: no failure inside the window and no running lock. Unknown
    usernames never succeed, so without this the table would only grow (review M4).

    Runs in its own short transaction AFTER the login transaction, and skips rows another
    transaction holds: purging inside the login transaction deadlocked two concurrent failures
    on two stale rows (review N1, test_throttle_concurrency.py)."""
    with transaction.atomic():
        stale = list(
            LoginThrottle.objects.select_for_update(skip_locked=True)
            .filter(updated_at__lt=now - max(WINDOW, LOCK_DURATION))
            .exclude(locked_until__gt=now)
            .values_list("pk", flat=True)
        )
        LoginThrottle.objects.filter(pk__in=stale).delete()


def log_in(request: HttpRequest, username: str, password: str) -> User:
    """Throttled login. Wrong password, unknown user and inactive account are indistinguishable."""
    key = normalize_username(username)
    if len(key) > MAX_LENGTH:  # "İ".lower() is two characters: no such account can exist (L1)
        raise InvalidCredentialsError
    now = timezone.now()
    # Decide inside the transaction, raise after it: raising inside would roll the failure back.
    with transaction.atomic():
        row = LoginThrottle.objects.select_for_update().filter(username=key).first()
        state = _state(row) if row else ThrottleState()
        user = None
        failed = False
        if not is_locked(state, now):
            user = authenticate(request, username=key, password=password)
            if isinstance(user, User):
                state = register_success()
                if row:
                    row.delete()  # the reset state is "no row"; a success never creates one
            else:
                # Created only on the first failure; get_or_create survives a concurrent first.
                row, _ = LoginThrottle.objects.select_for_update().get_or_create(username=key)
                state = register_failure(_state(row), now)
                _store(row, state, now)
                failed = True
    if failed:
        _purge_stale(now)  # outside the login transaction: no lock is held here (N1)
    if is_locked(state, now):
        raise LoginLockedError
    if not isinstance(user, User):
        raise InvalidCredentialsError
    login(request, user)
    return user


def log_out(request: HttpRequest) -> None:
    logout(request)


def change_password(request: HttpRequest, user: User, new_password: str) -> None:
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])
    update_session_auth_hash(request, user)  # keep this session, drop any other


def roles_of(user: User) -> list[Role]:
    return derive_roles(
        employee_active=is_employee_active(user.employee_id),
        has_active_reports=has_active_direct_reports(user.employee_id),
        is_hr=user.is_hr,
    )


def profile_of(user: User) -> dict[str, object]:
    """What the home page shows: own name, own roles and — for managers — own direct team."""
    employee = get_employee(user.employee_id)
    roles = roles_of(user)
    team = (
        [
            {"first_name": r.first_name, "last_name": r.last_name}
            for r in active_direct_reports(user.employee_id)
        ]
        if Role.MANAGER in roles
        else None
    )
    return {
        "first_name": employee.first_name if employee else "",
        "last_name": employee.last_name if employee else "",
        "roles": [str(role) for role in roles],
        "team": team,
    }
