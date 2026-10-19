"""Shared pytest setup.

- Every test under a ``tests/integration/`` directory is marked ``integration`` automatically, so
  the fast/full split in scripts/check.conf is a selector, never a list (docs/testing.md, rule 4).
- Integration tests get a throwaway PostgreSQL 17 from Testcontainers. The container starts only
  when a test needs the database and is stopped and removed at session end, failures included
  (docs/testing.md, Resource hygiene).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from django.conf import settings


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "integration" in Path(item.path).parts:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def django_db_modify_db_settings(
    django_db_modify_db_settings_parallel_suffix: None,
) -> Iterator[None]:
    from testcontainers.community.postgres import PostgresContainer

    container = PostgresContainer("postgres:17-alpine", driver=None)
    container.start()
    try:
        settings.DATABASES["default"].update(
            {
                "HOST": container.get_container_host_ip(),
                "PORT": str(container.get_exposed_port(5432)),
                "NAME": container.dbname,
                "USER": container.username,
                "PASSWORD": container.password,
            }
        )
        yield
    finally:
        container.stop()
