"""Tests enforcing that AI investigation code can never resolve a case.

Rule enforced: neither packages/application/.../investigation.py nor any
module under packages/ai/src may import the Resolution class or its
constructing module attribute. AI investigation may only ever produce an
Investigation and, optionally, a ResolutionProposal for a human to act on
through the existing HumanReviewUseCase - it must never construct a
Resolution itself.
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


def _imports_resolution(py_file: Path) -> list[str]:
    content = py_file.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(py_file))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "Resolution":
                    violations.append(f"{py_file}:{node.lineno} imports symbol 'Resolution'")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("Resolution"):
                    violations.append(f"{py_file}:{node.lineno} imports '{alias.name}'")
    return violations


def test_investigation_use_case_never_imports_resolution() -> None:
    root = get_project_root()
    target = (
        root / "packages" / "application" / "src" / "cashproof" / "application" / "investigation.py"
    )
    assert target.is_file(), "expected investigation.py to exist"

    violations = _imports_resolution(target)
    assert not violations, "AI investigation use case must never import Resolution:\n" + "\n".join(
        violations
    )


def test_ai_package_never_imports_resolution() -> None:
    root = get_project_root()
    ai_src = root / "packages" / "ai" / "src"

    violations: list[str] = []
    for py_file in find_python_files(ai_src):
        violations.extend(_imports_resolution(py_file))

    assert not violations, "packages/ai must never import Resolution:\n" + "\n".join(violations)
