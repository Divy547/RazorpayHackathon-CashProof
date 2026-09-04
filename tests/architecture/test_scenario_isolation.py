"""Tests enforcing ScenarioFamily technical isolation from production reconciliation code.

Rules enforced:
- ScenarioFamily is evaluator-only (benchmark taxonomy label).
- Production code MUST NOT import or reference ScenarioFamily.
"""

from __future__ import annotations

import ast
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def find_python_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [
        p for p in directory.rglob("*.py") if not p.name.startswith(".") and ".venv" not in p.parts
    ]


def test_production_modules_do_not_import_scenario_family() -> None:
    """Ensure no production code imports or references ScenarioFamily."""
    root = get_project_root()
    production_roots = [
        root / "packages" / "domain" / "src",
        root / "packages" / "application" / "src",
        root / "packages" / "infrastructure" / "src",
        root / "packages" / "ai" / "src",
        root / "apps" / "api" / "src",
    ]

    violations: list[str] = []

    for prod_root in production_roots:
        for py_file in find_python_files(prod_root):
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        if alias.name == "ScenarioFamily" or "scenario" in alias.name.lower():
                            rel = py_file.relative_to(root)
                            violations.append(
                                f"{rel}:{node.lineno} imports symbol '{alias.name}' from '{mod}'"
                            )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if "scenario" in alias.name.lower():
                            rel = py_file.relative_to(root)
                            violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")

    assert not violations, "ScenarioFamily isolation violations in production code:\n" + "\n".join(
        violations
    )
