"""Shared setup for the balances integration tests (real PostgreSQL via Testcontainers)."""

import datetime
from collections.abc import Callable

import pytest

from balances.api import set_start_date
from tests.factories import Employee, create_employee

D = datetime.date
HIRE = D(2020, 3, 10)
BORN = D(1990, 1, 1)


@pytest.fixture
def started(db: None) -> None:
    """Automatic accruals on from a date before every anniversary used here."""
    set_start_date(D(2020, 1, 1))


@pytest.fixture
def employee(db: None) -> Employee:
    return create_employee("Ece", "Demir", hire_date=HIRE, birth_date=BORN)


@pytest.fixture
def make_employee(db: None) -> Callable[..., Employee]:
    return create_employee
