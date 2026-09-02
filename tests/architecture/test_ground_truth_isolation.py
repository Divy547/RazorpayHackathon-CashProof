"""Tests enforcing GroundTruth technical isolation.

Rules enforced:
- GroundTruth is evaluator-only.
- Production code MUST NOT import or reference GroundTruth.
- GroundTruth queries, entities, and evaluator access remain strictly confined
  to benchmark evaluator.
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


def test_production_modules_do_not_import_ground_truth() -> None:
    """Ensure no production code imports or accesses ground_truth."""
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
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if (
                            "ground_truth" in alias.name.lower()
                            or "groundtruth" in alias.name.lower()
                        ):
                            rel = py_file.relative_to(root)
                            violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if "ground_truth" in mod.lower() or "groundtruth" in mod.lower():
                        rel = py_file.relative_to(root)
                        violations.append(f"{rel}:{node.lineno} imports from '{mod}'")
                    for alias in node.names:
                        if "groundtruth" in alias.name.lower() or alias.name == "GroundTruth":
                            rel = py_file.relative_to(root)
                            violations.append(f"{rel}:{node.lineno} imports symbol '{alias.name}'")

    assert not violations, "GroundTruth isolation violations in production code:\n" + "\n".join(
        violations
    )


def test_source_entities_contain_no_decoy_or_scenario_flags() -> None:
    """Verify source domain models do not define decoy, noise, or scenario flags."""
    root = get_project_root()
    domain_src = root / "packages" / "domain" / "src"

    forbidden_identifiers = {
        "is_decoy",
        "is_noise",
        "scenario_label",
        "scenario_type",
        "ground_truth_id",
        "is_truth",
        "is_corrupted",
    }

    violations: list[str] = []
    for py_file in find_python_files(domain_src):
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        rel = py_file.relative_to(root)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.lower() in forbidden_identifiers:
                    violations.append(
                        f"{rel}:{node.lineno} defines prohibited identifier '{node.name}'"
                    )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id.lower() in forbidden_identifiers:
                    violations.append(
                        f"{rel}:{node.lineno} defines prohibited field '{node.target.id}'"
                    )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.lower() in forbidden_identifiers:
                        violations.append(
                            f"{rel}:{node.lineno} assigns prohibited variable '{target.id}'"
                        )

    assert not violations, "Source entity label leak violations:\n" + "\n".join(violations)
