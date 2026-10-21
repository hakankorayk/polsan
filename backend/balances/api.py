"""Public interface of the balances module.

Other modules may import only this module (docs/architecture.md, Forbidden dependencies 1).
"""

import datetime

from balances import clock
from balances.domain.amounts import AdjustmentError, validate_adjustment_amount, validate_reason
from balances.models import ImmutableEntryError
from balances.services import (
    BalanceSummary,
    EmployeeNotFoundError,
    EntryView,
    StartDateLockedError,
    add_adjustment,
    after_employee_change,
    balance_of,
    before_employee_change,
    check_start_date_change,
    materialize_accruals,
    set_start_date,
    start_date,
    start_date_locked,
    summary_of,
)

__all__ = [
    "AdjustmentError",
    "BalanceSummary",
    "EmployeeNotFoundError",
    "EntryView",
    "ImmutableEntryError",
    "StartDateLockedError",
    "add_adjustment",
    "after_employee_change",
    "check_start_date_change",
    "balance_of",
    "before_employee_change",
    "materialize_accruals",
    "set_start_date",
    "start_date",
    "start_date_locked",
    "summary_of",
    "today",
    "validate_adjustment_amount",
    "validate_reason",
]


def today() -> datetime.date:
    """The date accruals are computed for (Europe/Istanbul); callers outside the module use it."""
    return clock.today()
