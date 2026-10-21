"""Role derivation (spec 0002, AC-4; docs/domain.md: a role, not a job title). Pure Python."""

from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"


def derive_roles(*, employee_active: bool, has_active_reports: bool, is_hr: bool) -> list[Role]:
    """Every active employee is EMPLOYEE; MANAGER needs at least one active direct report;
    HR is granted explicitly. An inactive employee has no role."""
    if not employee_active:
        return []
    roles = [Role.EMPLOYEE]
    if has_active_reports:
        roles.append(Role.MANAGER)
    if is_hr:
        roles.append(Role.HR)
    return roles
