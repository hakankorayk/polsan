"""Balance API (spec 0003). Only the signed-in employee's own data: there is no id parameter, so
another employee's balance cannot even be addressed (AC-29; plan 0003, risk 5)."""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from balances import clock, services
from balances.serializers import BalanceSummarySerializer


class BalanceView(APIView):
    # Default deny, stated explicitly: authenticated + password change completed (settings).
    # api_settings resolves the dotted paths to classes; the stubs still type them as str.
    permission_classes: list[type[BasePermission]] = list(
        api_settings.DEFAULT_PERMISSION_CLASSES  # type: ignore[arg-type]
    )

    @extend_schema(operation_id="balance_retrieve", responses={200: BalanceSummarySerializer})
    def get(self, request: Request) -> Response:
        # AUTH_USER_MODEL contract: every account is bound to one employee (docs/architecture.md).
        # balances may not import identity, so it reads the attribute, not the model.
        employee_id: int = request.user.employee_id  # type: ignore[union-attr]
        summary = services.summary_of(employee_id, clock.today())
        return Response(BalanceSummarySerializer(summary).data)
