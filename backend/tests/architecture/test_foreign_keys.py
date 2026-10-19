"""AC-10 (rule 4): cross-module relations point only at employees.Employee."""

from django.apps import apps
from django.db.models import Model

from tests.architecture.checks import foreign_key_violations


def _project_relations() -> list[tuple[str, str]]:
    return [
        (f"{model._meta.label}.{field.name}", field.related_model._meta.label)
        for model in apps.get_models()
        for field in model._meta.get_fields()
        if field.is_relation
        and not field.auto_created
        and isinstance(field.related_model, type)
        and issubclass(field.related_model, Model)
    ]


def test_cross_module_fk_only_to_employee() -> None:
    assert foreign_key_violations(_project_relations()) == []


def test_checker_flags_fk_to_other_module() -> None:
    relations = [
        ("leaves.LeaveRequest.employee", "employees.Employee"),
        ("leaves.LeaveRequest.ledger_entry", "balances.LedgerEntry"),
        ("leaves.LeaveRequest.type", "leaves.LeaveType"),
        ("leaves.LeaveRequest.created_by", "auth.User"),
    ]

    assert foreign_key_violations(relations) == [
        "leaves.LeaveRequest.ledger_entry -> balances.LedgerEntry (only employees.Employee)"
    ]
