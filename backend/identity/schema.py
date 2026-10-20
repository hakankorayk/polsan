"""OpenAPI: document CsrfAwareSessionAuthentication exactly like DRF's session cookie auth."""

from drf_spectacular.authentication import SessionScheme


class CsrfAwareSessionScheme(SessionScheme):
    target_class = "identity.authentication.CsrfAwareSessionAuthentication"
