from django.urls import path

from identity.views import CsrfView, LoginView, LogoutView, MeView, PasswordChangeView

urlpatterns = [
    path("api/auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/password/", PasswordChangeView.as_view(), name="auth-password"),
    path("api/me/", MeView.as_view(), name="me"),
]
