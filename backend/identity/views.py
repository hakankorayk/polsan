"""Authentication API (spec 0002). Errors are DRF exceptions rendered as problem+json."""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authentication import BaseAuthentication, CSRFCheck
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from identity import services
from identity.authentication import CsrfAwareSessionAuthentication, CsrfFailedAPIError
from identity.models import User
from identity.permissions import PasswordChangeCompleted
from identity.serializers import (
    LoginResultSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileSerializer,
)


class InvalidCredentialsAPIError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_credentials"
    default_detail = "Kullanıcı adı veya parola hatalı."


class LoginLockedAPIError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "login_locked"
    default_detail = "Çok fazla hatalı deneme. Lütfen 15 dakika sonra tekrar deneyin."


class PasswordChangeNotRequiredAPIError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "password_change_not_required"
    default_detail = "Parola değişikliği yalnızca geçici parolayla giriş yapıldığında yapılabilir."


def _enforce_csrf(request: Request) -> None:
    """DRF skips CSRF for anonymous requests; login must not (spec 0002, AC-19)."""
    check = CSRFCheck(lambda _request: None)  # type: ignore[arg-type]
    check.process_request(request)
    if check.process_view(request, None, (), {}):  # type: ignore[arg-type]
        raise CsrfFailedAPIError


def _user(request: Request) -> User:
    user = request.user
    if not isinstance(user, User):  # unreachable behind IsAuthenticated; keeps types honest
        raise PermissionDenied
    return user


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes: list[type[BasePermission]] = [AllowAny]

    @extend_schema(operation_id="auth_csrf", responses={204: None}, auth=[])
    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes: list[type[BasePermission]] = [AllowAny]

    @extend_schema(
        operation_id="auth_login",
        request=LoginSerializer,
        responses={200: LoginResultSerializer},
        auth=[],
    )
    def post(self, request: Request) -> Response:
        _enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.log_in(
                request._request,
                serializer.validated_data["username"],
                serializer.validated_data["password"],
            )
        except services.LoginLockedError as error:
            raise LoginLockedAPIError from error
        except services.InvalidCredentialsError as error:
            raise InvalidCredentialsAPIError from error
        return Response({"must_change_password": user.must_change_password})


class LogoutView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = [CsrfAwareSessionAuthentication]
    permission_classes: list[type[BasePermission]] = [IsAuthenticated]

    @extend_schema(operation_id="auth_logout", request=None, responses={204: None})
    def post(self, request: Request) -> Response:
        services.log_out(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = [CsrfAwareSessionAuthentication]
    permission_classes: list[type[BasePermission]] = [IsAuthenticated]

    @extend_schema(
        operation_id="auth_password_change", request=PasswordChangeSerializer, responses={204: None}
    )
    def post(self, request: Request) -> Response:
        user = _user(request)
        if not user.must_change_password:
            raise PasswordChangeNotRequiredAPIError
        serializer = PasswordChangeSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        services.change_password(request._request, user, serializer.validated_data["new_password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    authentication_classes: list[type[BaseAuthentication]] = [CsrfAwareSessionAuthentication]
    permission_classes: list[type[BasePermission]] = [IsAuthenticated, PasswordChangeCompleted]

    @extend_schema(operation_id="me_retrieve", responses={200: ProfileSerializer})
    def get(self, request: Request) -> Response:
        return Response(ProfileSerializer(services.profile_of(_user(request))).data)
