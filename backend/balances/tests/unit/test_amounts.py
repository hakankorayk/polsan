"""Spec 0003 — AC-17: adjustment amount and reason rules (BR-5, BR-12)."""

from decimal import Decimal

import pytest

from balances.domain.amounts import AdjustmentError, validate_adjustment_amount, validate_reason


@pytest.mark.parametrize("amount", ["0.5", "-0.5", "14", "-2", "100", "-100", "12.5"])
def test_valid_amounts_accepted(amount: str) -> None:
    validate_adjustment_amount(Decimal(amount))


@pytest.mark.parametrize(
    ("amount", "code"),
    [
        ("0", "amount_zero"),
        ("1.3", "amount_not_half_multiple"),
        ("-0.2", "amount_not_half_multiple"),
        ("100.5", "amount_too_large"),
        ("-101", "amount_too_large"),
    ],
)
def test_invalid_amounts_rejected(amount: str, code: str) -> None:
    with pytest.raises(AdjustmentError) as error:
        validate_adjustment_amount(Decimal(amount))

    assert (error.value.field, error.value.code) == ("amount", code)


@pytest.mark.parametrize("reason", ["", "   ", "\t\n"])
def test_br12_empty_or_blank_reason_rejected(reason: str) -> None:
    with pytest.raises(AdjustmentError) as error:
        validate_reason(reason)

    assert (error.value.field, error.value.code) == ("reason", "reason_required")


def test_reason_is_trimmed() -> None:
    assert validate_reason("  Açılış bakiyesi ") == "Açılış bakiyesi"
