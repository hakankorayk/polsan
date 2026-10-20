"""Public interface of the identity module.

Other modules may import only this module (docs/architecture.md, Forbidden dependencies 1).
"""

from identity.models import User

__all__ = ["active_hr_count", "is_last_active_hr"]


def active_hr_count() -> int:
    """Accounts that can act as HR right now: active account, HR grant, active employee."""
    return User.objects.filter(is_hr=True, is_active=True, employee__is_active=True).count()


def is_last_active_hr(*, user_id: int | None = None, employee_id: int | None = None) -> bool:
    """True if the given account (or the account of the given employee) is the only active HR."""
    accounts = User.objects.filter(is_hr=True, is_active=True, employee__is_active=True)
    if user_id is not None:
        accounts = accounts.filter(pk=user_id)
    elif employee_id is not None:
        accounts = accounts.filter(employee_id=employee_id)
    else:
        return False
    return accounts.exists() and active_hr_count() == 1
