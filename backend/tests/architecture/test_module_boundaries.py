"""AC-8, AC-9 (rule 1), AC-10 (rule 5): modules, public interfaces, no signals."""

import importlib

import grimp
from django.apps import apps

from tests.architecture.checks import (
    MODULES,
    internal_import_violations,
    module_source_files,
    signal_import_violations,
)


def _project_imports() -> list[tuple[str, str]]:
    graph = grimp.build_graph(*MODULES, "config")
    return [
        (importer, imported)
        for importer in graph.modules
        for imported in graph.find_modules_directly_imported_by(importer)
    ]


def test_six_modules_exist_with_public_api() -> None:
    for module in MODULES:
        assert apps.is_installed(module), module
        api = importlib.import_module(f"{module}.api")
        assert isinstance(api.__all__, list), f"{module}.api must declare __all__"


def test_only_public_api_is_imported() -> None:
    assert internal_import_violations(_project_imports()) == []


def test_checker_flags_internal_import() -> None:
    imports = [
        ("leaves.services", "balances.api"),
        ("leaves.services", "balances.models"),
        ("leaves.views", "leaves.models"),
    ]

    assert internal_import_violations(imports) == [
        "leaves.services imports balances.models (only balances.api is public)"
    ]


def test_no_signal_receivers() -> None:
    assert signal_import_violations(module_source_files()) == []


def test_checker_flags_signal_import() -> None:
    sources = [
        ("leaves/a.py", "from django.dispatch import receiver\n"),
        ("leaves/b.py", "from django.db.models.signals import post_save\n"),
        ("leaves/c.py", "from django.db.models import signals\n"),
        ("leaves/d.py", "import django.dispatch\n"),
        ("leaves/ok.py", "from django.db import models\n"),
    ]

    assert len(signal_import_violations(sources)) == 4
