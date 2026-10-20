"""Spec 0002 — AC-4: role derivation."""

from identity.domain.roles import Role, derive_roles


def test_active_employee_is_employee_only() -> None:
    assert derive_roles(employee_active=True, has_active_reports=False, is_hr=False) == [
        Role.EMPLOYEE
    ]


def test_manager_needs_an_active_direct_report() -> None:
    assert derive_roles(employee_active=True, has_active_reports=True, is_hr=False) == [
        Role.EMPLOYEE,
        Role.MANAGER,
    ]


def test_hr_is_granted_and_roles_combine() -> None:
    assert derive_roles(employee_active=True, has_active_reports=True, is_hr=True) == [
        Role.EMPLOYEE,
        Role.MANAGER,
        Role.HR,
    ]
    assert derive_roles(employee_active=True, has_active_reports=False, is_hr=True) == [
        Role.EMPLOYEE,
        Role.HR,
    ]


def test_inactive_employee_has_no_role() -> None:
    assert derive_roles(employee_active=False, has_active_reports=True, is_hr=True) == []
