"""AC-2 (server side): healthy against a real PostgreSQL."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_ok_with_database() -> None:
    response = APIClient().get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
