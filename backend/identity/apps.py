from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity"

    def ready(self) -> None:
        from identity import schema  # noqa: F401, PLC0415 — registers the OpenAPI extension
