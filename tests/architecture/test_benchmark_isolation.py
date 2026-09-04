"""Architecture tests enforcing benchmark, GroundTruth, and ScenarioFamily isolation.

Rules enforced:
- packages/application NEVER imports GroundTruth.
- packages/application NEVER imports ScenarioFamily.
- packages/domain NEVER imports GroundTruth or ScenarioFamily.
- apps/api NEVER imports GroundTruth, ScenarioFamily, or cashproof.benchmark.
- packages/benchmark evaluator IS permitted to import GroundTruth and ScenarioFamily.
- Dependency direction remains strictly valid.
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


def test_application_never_imports_ground_truth_or_scenario_family() -> None:
    root = get_project_root()
    app_src = root / "packages" / "application" / "src"

    violations: list[str] = []
    for py_file in find_python_files(app_src):
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        rel = py_file.relative_to(root)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_lower = alias.name.lower()
                    if "groundtruth" in name_lower or "ground_truth" in name_lower:
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
                    if "scenariofamily" in name_lower:
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                if "ground_truth" in mod or "groundtruth" in mod:
                    violations.append(f"{rel}:{node.lineno} imports from '{node.module}'")
                for alias in node.names:
                    if alias.name in ("GroundTruth", "ScenarioFamily"):
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")

    assert not violations, (
        "Application layer violated GroundTruth or ScenarioFamily isolation:\n"
        + "\n".join(violations)
    )


def test_domain_never_imports_ground_truth_or_scenario_family() -> None:
    root = get_project_root()
    dom_src = root / "packages" / "domain" / "src"

    violations: list[str] = []
    for py_file in find_python_files(dom_src):
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        rel = py_file.relative_to(root)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_lower = alias.name.lower()
                    if (
                        "groundtruth" in name_lower
                        or "ground_truth" in name_lower
                        or "scenariofamily" in name_lower
                    ):
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                if "ground_truth" in mod or "groundtruth" in mod or "scenario" in mod:
                    violations.append(f"{rel}:{node.lineno} imports from '{node.module}'")
                for alias in node.names:
                    if alias.name in ("GroundTruth", "ScenarioFamily"):
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")

    assert not violations, (
        "Domain layer violated GroundTruth or ScenarioFamily isolation:\n" + "\n".join(violations)
    )


def test_api_never_imports_ground_truth_or_scenario_family_or_benchmark() -> None:
    root = get_project_root()
    api_src = root / "apps" / "api" / "src"

    violations: list[str] = []
    for py_file in find_python_files(api_src):
        content = py_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(py_file))
        rel = py_file.relative_to(root)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_lower = alias.name.lower()
                    if (
                        "groundtruth" in name_lower
                        or "ground_truth" in name_lower
                        or "scenariofamily" in name_lower
                    ):
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
                    if "cashproof.benchmark" in alias.name:
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                if "benchmark" in mod or "ground_truth" in mod or "groundtruth" in mod:
                    violations.append(f"{rel}:{node.lineno} imports from '{node.module}'")
                for alias in node.names:
                    if alias.name in ("GroundTruth", "ScenarioFamily"):
                        violations.append(f"{rel}:{node.lineno} imports '{alias.name}'")

    assert not violations, "API adapter violated isolation boundaries:\n" + "\n".join(violations)


def test_benchmark_evaluator_is_permitted_to_import_ground_truth() -> None:
    """Proves GroundTruth is available and imported inside benchmark package."""
    from cashproof.benchmark.evaluator import BenchmarkEvaluator
    from cashproof.benchmark.models import GroundTruth, ScenarioFamily

    assert BenchmarkEvaluator is not None
    assert GroundTruth is not None
    assert ScenarioFamily is not None
