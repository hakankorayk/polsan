"""Spec 0002 — AC-2 (no self-management, no cycles) and AC-16 (Turkish sorting)."""

import pytest

from employees.domain.hierarchy import HierarchyError, turkish_sort_key, validate_manager


def _tree(**managers: str | None):
    return lambda employee: managers.get(employee)


def test_self_manager_rejected() -> None:
    with pytest.raises(HierarchyError) as error:
        validate_manager("a", "a", _tree())

    assert error.value.code == "self_manager"


def test_two_and_three_step_cycles_rejected() -> None:
    # A -> B -> A
    with pytest.raises(HierarchyError) as two_step:
        validate_manager("a", "b", _tree(b="a"))
    # A -> B -> C -> A
    with pytest.raises(HierarchyError) as three_step:
        validate_manager("a", "b", _tree(b="c", c="a"))

    assert two_step.value.code == "manager_cycle"
    assert three_step.value.code == "manager_cycle"


def test_valid_chains_accepted() -> None:
    validate_manager("a", "b", _tree(b="c", c=None))
    validate_manager("a", None, _tree())
    validate_manager(None, "b", _tree(b="a"))  # new employee: cannot be in a cycle yet


def test_existing_loop_elsewhere_does_not_hang() -> None:
    validate_manager("a", "b", _tree(b="c", c="b"))


def test_turkish_sort_key() -> None:
    names = ["Yılmaz", "Çelik", "Şahin", "Demir", "İnce", "Işık", "Öztürk", "Uğur", "Cengiz"]

    assert sorted(names, key=turkish_sort_key) == [
        "Cengiz",
        "Çelik",
        "Demir",
        "Işık",
        "İnce",
        "Öztürk",
        "Şahin",
        "Uğur",
        "Yılmaz",
    ]
