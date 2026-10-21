from django.urls import include, path

from config.admin import hr_admin_site
from config.health import HealthView

urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("", include("identity.urls")),
    path("admin/", hr_admin_site.urls),
]
