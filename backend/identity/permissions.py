"""Spec 0002, AC-10: a temporary password gives access to nothing but the password change."""

from typing import TYPE_CHECKING

from rest_framework.permissions import BasePermission

if TYPE_CHECKING:  # DRF loads this module from its settings while rest_framework.views imports
    from rest_framework.request import Request
    from rest_framework.views import APIView


class PasswordChangeCompleted(BasePermission):
    message = "Devam etmeden önce parolanızı değiştirmelisiniz."
    code = "password_change_required"

    def has_permission(self, request: "Request", view: "APIView") -> bool:
        return not getattr(request.user, "must_change_password", False)
