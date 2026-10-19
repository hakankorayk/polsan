"""Architecture rules that import-linter cannot express (docs/architecture.md, Forbidden
dependencies 1, 4, 5 and the default-deny rule of docs/security.md).

Each checker takes plain data and returns human-readable violations, so the tests can feed it the
real project and, separately, a deliberate violation proving the checker catches it.
"""

import ast
from collections.abc import Iterable
from pathlib import Path

MODULES = ("employees", "workcalendar", "balances", "leaves", "identity", "audit")
FK_TARGET_ALLOWED_ACROSS_MODULES = "employees.Employee"
SIGNAL_MODULES = ("django.dispatch", "django.db.models.signals", "django.core.signals")
BACKEND_DIR = Path(__file__).resolve().parents[2]


def internal_import_violations(imports: Iterable[tuple[str, str]]) -> list[str]:
    """Rule 1: a module imports another module only through its public ``api``."""
    violations = []
    for importer, imported in imports:
        source, target = importer.split(".")[0], imported.split(".")[0]
        if source not in MODULES or target not in MODULES or source == target:
            continue
        if imported not in (target, f"{target}.api"):
            violations.append(f"{importer} imports {imported} (only {target}.api is public)")
    return violations


def signal_import_violations(sources: Iterable[tuple[str, str]]) -> list[str]:
    """Rule 5: no Django signals in business modules. ``sources`` = (file name, source code)."""
    violations = []
    for filename, source in sources:
        for node in ast.walk(ast.parse(source, filename=filename)):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
            for name in names:
                if any(name == m or name.startswith(f"{m}.") for m in SIGNAL_MODULES):
                    violations.append(f"{filename}:{getattr(node, 'lineno', 0)} imports {name}")
                    break
    return violations


def foreign_key_violations(relations: Iterable[tuple[str, str]]) -> list[str]:
    """Rule 4: across modules, a relation may only point at employees.Employee.

    ``relations`` = (source "app.Model.field", target "app.Model").
    """
    violations = []
    for source, target in relations:
        source_app, target_app = source.split(".")[0], target.split(".")[0]
        if source_app not in MODULES or target_app not in MODULES or source_app == target_app:
            continue
        if target != FK_TARGET_ALLOWED_ACROSS_MODULES:
            violations.append(f"{source} -> {target} (only {FK_TARGET_ALLOWED_ACROSS_MODULES})")
    return violations


def undeclared_permission_violations(routes: Iterable[tuple[str, type | None]]) -> list[str]:
    """Default deny: every route is a DRF view that declares ``permission_classes`` itself
    (or through a project base class). ``routes`` = (route, DRF view class or None)."""
    violations = []
    for route, view_class in routes:
        if view_class is None:
            violations.append(f"{route}: not a DRF view, permissions cannot be enforced")
            continue
        declaring = next(
            (
                klass
                for klass in view_class.__mro__
                if not klass.__module__.startswith("rest_framework")
                and "permission_classes" in vars(klass)
            ),
            None,
        )
        if declaring is None:
            violations.append(f"{route}: {view_class.__qualname__} declares no permission_classes")
        elif not vars(declaring)["permission_classes"]:
            # An empty list is open access in disguise; open access must say AllowAny.
            violations.append(
                f"{route}: {view_class.__qualname__} declares empty permission_classes "
                "(open access must be an explicit AllowAny)"
            )
    return violations


def module_source_files() -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(BACKEND_DIR)), path.read_text(encoding="utf-8"))
        for module in MODULES
        for path in sorted((BACKEND_DIR / module).rglob("*.py"))
    ]
