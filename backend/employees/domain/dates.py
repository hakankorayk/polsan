"""Birth date rules (spec 0003, Requirement 1; AC-2). Pure Python: "today" is passed in."""

import datetime


class BirthDateError(Exception):
    """A birth date that the employee record may not hold."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_birth_date(
    birth: datetime.date, hire: datetime.date | None, today: datetime.date
) -> None:
    if birth > today:
        raise BirthDateError("birth_date_in_future", "Doğum tarihi bugünden sonra olamaz.")
    if hire is not None and birth >= hire:
        raise BirthDateError(
            "birth_date_not_before_hire", "Doğum tarihi işe giriş tarihinden önce olmalıdır."
        )
