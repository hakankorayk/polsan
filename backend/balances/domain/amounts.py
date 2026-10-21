"""HR adjustment input rules (docs/domain.md BR-5, BR-12; spec 0003, Req 7; AC-17). Pure Python."""

from decimal import Decimal

MAX_ADJUSTMENT_DAYS = Decimal(100)


class AdjustmentError(Exception):
    """An adjustment the ledger may not hold; ``field`` names the input at fault."""

    def __init__(self, field: str, code: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.code = code
        self.message = message


def validate_adjustment_amount(amount: Decimal) -> None:
    if amount == 0:
        raise AdjustmentError("amount", "amount_zero", "Miktar sıfır olamaz.")
    if (amount * 2) % 1 != 0:
        raise AdjustmentError("amount", "amount_not_half_multiple", "Miktar 0,5'in katı olmalıdır.")
    if abs(amount) > MAX_ADJUSTMENT_DAYS:
        raise AdjustmentError("amount", "amount_too_large", "Miktar en fazla 100 gün olabilir.")


def validate_reason(reason: str) -> str:
    """Return the reason without surrounding whitespace; an empty one is refused."""
    cleaned = reason.strip()
    if not cleaned:
        raise AdjustmentError("reason", "reason_required", "Gerekçe zorunludur.")
    return cleaned
