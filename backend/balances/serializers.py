from rest_framework import serializers

from balances.models import LedgerKind


class NextAccrualSerializer(serializers.Serializer[object]):
    date = serializers.DateField()
    days = serializers.DecimalField(max_digits=5, decimal_places=1)


class LedgerEntrySerializer(serializers.Serializer[object]):
    id = serializers.UUIDField(source="public_id")
    date = serializers.DateField(source="effective_date")
    kind = serializers.ChoiceField(choices=LedgerKind.choices)
    amount = serializers.DecimalField(max_digits=5, decimal_places=1)
    reason = serializers.SerializerMethodField()

    def get_reason(self, entry: object) -> str | None:
        """Adjustments carry HR's reason; accruals have none."""
        reason = getattr(entry, "reason", "")
        return reason or None


# The signed-in employee's own balance (spec 0003, Req 11). No birth date, ever (AC-3).
# (A comment, not a docstring: docstrings become descriptions in the public OpenAPI schema.)
class BalanceSummarySerializer(serializers.Serializer[object]):
    balance = serializers.DecimalField(max_digits=6, decimal_places=1)
    next_accrual = NextAccrualSerializer(allow_null=True)
    entries = LedgerEntrySerializer(many=True)
