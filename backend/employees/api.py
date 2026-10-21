"""Public interface of the employees module.

Other modules may import only this module (docs/architecture.md, Forbidden dependencies 1).
"""

import datetime
import uuid
from dataclasses import dataclass

from employees.domain.hierarchy import turkish_sort_key
from employees.models import Employee

__all__ = [
    "EmployeeInfo",
    "active_direct_reports",
    "create_employee",
    "get_employee",
    "has_active_direct_reports",
    "is_employee_active",
]


@dataclass(frozen=True)
class EmployeeInfo:
    public_id: uuid.UUID
    first_name: str
    last_name: str
    is_active: bool


def _info(employee: Employee) -> EmployeeInfo:
    return EmployeeInfo(
        public_id=employee.public_id,
        first_name=employee.first_name,
        last_name=employee.last_name,
        is_active=employee.is_active,
    )


def create_employee(first_name: str, last_name: str, hire_date: datetime.date) -> int:
    """Create an employee with no manager; returns its id (used by `create_first_hr`)."""
    employee = Employee(first_name=first_name, last_name=last_name, hire_date=hire_date)
    employee.full_clean()
    employee.save()
    return employee.pk


def get_employee(employee_id: int) -> EmployeeInfo | None:
    employee = Employee.objects.filter(pk=employee_id).first()
    return _info(employee) if employee else None


def is_employee_active(employee_id: int) -> bool:
    return Employee.objects.filter(pk=employee_id, is_active=True).exists()


def has_active_direct_reports(employee_id: int) -> bool:
    return Employee.objects.filter(manager_id=employee_id, is_active=True).exists()


def active_direct_reports(employee_id: int) -> list[EmployeeInfo]:
    """Direct, active reports only, sorted by last name then first name (Turkish alphabet)."""
    reports = [_info(e) for e in Employee.objects.filter(manager_id=employee_id, is_active=True)]
    return sorted(
        reports, key=lambda e: (turkish_sort_key(e.last_name), turkish_sort_key(e.first_name))
    )
