"""Organisation tree rules (docs/domain.md; spec 0002, AC-2 and AC-16). Pure Python."""

from collections.abc import Callable, Hashable

TURKISH_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"
_POSITION = {letter: index for index, letter in enumerate(TURKISH_ALPHABET)}


class HierarchyError(Exception):
    """A manager assignment that would break the organisation tree."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_manager[Id: Hashable](
    employee_id: Id | None, new_manager_id: Id | None, manager_of: Callable[[Id], Id | None]
) -> None:
    """Raise HierarchyError if ``new_manager_id`` cannot manage ``employee_id``.

    ``manager_of`` returns the current manager of an employee (or None). A new, unsaved employee
    (``employee_id`` None) cannot be part of a cycle yet.
    """
    if new_manager_id is None or employee_id is None:
        return
    if new_manager_id == employee_id:
        raise HierarchyError("self_manager", "Bir çalışan kendi yöneticisi olamaz.")
    seen: set[Id] = set()
    current: Id | None = new_manager_id
    while current is not None and current not in seen:
        if current == employee_id:
            raise HierarchyError("manager_cycle", "Bu atama yönetici zincirinde döngü oluşturur.")
        seen.add(current)
        current = manager_of(current)


_CIRCUMFLEX = str.maketrans({"â": "a", "î": "i", "û": "u"})


def turkish_sort_key(text: str) -> tuple[int, ...]:
    """Sort key following the Turkish alphabet (ç after c, ı before i, ş after s ...).
    â/î/û sort as a/i/u (Kâmil next to Kamil); a space sorts before every letter, so
    multi-word surnames stay next to their first word."""
    lowered = text.replace("I", "ı").replace("İ", "i").lower().translate(_CIRCUMFLEX)
    return tuple(
        -1 if char == " " else _POSITION.get(char, len(TURKISH_ALPHABET) + ord(char))
        for char in lowered
    )
