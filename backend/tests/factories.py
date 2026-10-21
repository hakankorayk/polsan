"""Test data factories shared across modules. They live outside every module, so creating an
employee for an identity test does not break rule 1 (only `<module>.api` is public)."""

import datetime

from employees.models import Employee

__all__ = ["Employee", "create_employee", "find_employee"]


def create_employee(
    first: str = "Ayşe",
    last: str = "Yılmaz",
    manager: Employee | None = None,
    active: bool = True,
    hire_date: datetime.date = datetime.date(2020, 1, 1),
    birth_date: datetime.date = datetime.date(1990, 1, 1),
) -> Employee:
    return Employee.objects.create(
        first_name=first,
        last_name=last,
        hire_date=hire_date,
        birth_date=birth_date,
        manager=manager,
        is_active=active,
    )


def find_employee(first_name: str) -> Employee:
    return Employee.objects.get(first_name=first_name)
