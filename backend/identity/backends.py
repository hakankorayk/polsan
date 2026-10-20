"""Authentication backend: case-insensitive usernames, and an account works only while both the
account and its employee are active. Django re-checks this on every request (get_user), so a
deactivated user's open session ends at the next request (spec 0002, AC-7, AC-26, AC-28)."""

from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from employees.api import is_employee_active
from identity.domain.usernames import normalize_username
from identity.models import User


class EmployeeAwareBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if username is None or password is None:
            return None
        return super().authenticate(
            request, username=normalize_username(username), password=password, **kwargs
        )

    def user_can_authenticate(self, user: User | AnonymousUser | None) -> bool:
        employee_id = getattr(user, "employee_id", None)
        return (
            super().user_can_authenticate(user)
            and employee_id is not None
            and is_employee_active(employee_id)
        )
