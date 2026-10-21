from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from identity.domain.roles import Role


class LoginSerializer(serializers.Serializer[dict[str, str]]):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=4096, trim_whitespace=False)


class LoginResultSerializer(serializers.Serializer[dict[str, bool]]):
    must_change_password = serializers.BooleanField()


class PasswordChangeSerializer(serializers.Serializer[dict[str, str]]):
    new_password = serializers.CharField(max_length=4096, trim_whitespace=False)
    new_password_confirm = serializers.CharField(max_length=4096, trim_whitespace=False)

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        user = self.context["user"]
        new = attrs["new_password"]
        if new != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Parolalar eşleşmiyor."})
        if user.check_password(new):
            raise serializers.ValidationError(
                {"new_password": "Yeni parola geçici parolayla aynı olamaz."}
            )
        try:
            validate_password(new, user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"new_password": list(error.messages)}) from error
        return attrs


class TeamMemberSerializer(serializers.Serializer[dict[str, str]]):
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class ProfileSerializer(serializers.Serializer[dict[str, Any]]):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    roles = serializers.ListField(child=serializers.ChoiceField(choices=[r.value for r in Role]))
    team = TeamMemberSerializer(many=True, allow_null=True)
