from django.urls import include, path

from config.health import HealthView

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("", include("identity.urls")),
]
