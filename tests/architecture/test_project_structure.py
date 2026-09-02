"""Tests validating project directory layout and canonical structure."""

from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def test_canonical_directories_exist() -> None:
    """Ensure all required root directories exist."""
    root = get_project_root()

    required_dirs = [
        root / "docs",
        root / "apps" / "api",
        root / "apps" / "cli",
        root / "packages" / "domain",
        root / "packages" / "application",
        root / "packages" / "infrastructure",
        root / "packages" / "ai",
        root / "packages" / "benchmark",
        root / "tests" / "architecture",
        root / "tests" / "domain",
        root / "tests" / "application",
        root / "tests" / "infrastructure",
        root / "tests" / "ai",
        root / "tests" / "benchmark",
        root / "datasets",
        root / "frontend",
    ]

    missing = [str(d.relative_to(root)) for d in required_dirs if not d.is_dir()]
    assert not missing, f"Missing required directories: {missing}"


def test_canonical_documentation_files_exist() -> None:
    """Ensure all canonical architecture and domain documentation files exist."""
    root = get_project_root()

    required_docs = [
        root / "AGENTS.md",
        root / "README.md",
        root / "docs" / "ARCHITECTURE.md",
        root / "docs" / "DOMAIN.md",
        root / "docs" / "DECISIONS.md",
        root / "docs" / "AI_BOUNDARIES.md",
        root / "docs" / "BENCHMARK.md",
        root / "docs" / "DEVELOPMENT.md",
    ]

    missing = [str(f.relative_to(root)) for f in required_docs if not f.is_file()]
    assert not missing, f"Missing required documentation files: {missing}"


def test_package_metadata_and_pytyped_markers_exist() -> None:
    """Ensure each package and app contains pyproject.toml, __init__.py, and py.typed."""
    root = get_project_root()

    targets = [
        ("packages/domain", root / "packages/domain/src/cashproof/domain"),
        ("packages/application", root / "packages/application/src/cashproof/application"),
        ("packages/infrastructure", root / "packages/infrastructure/src/cashproof/infrastructure"),
        ("packages/ai", root / "packages/ai/src/cashproof/ai"),
        ("packages/benchmark", root / "packages/benchmark/src/cashproof/benchmark"),
        ("apps/api", root / "apps/api/src/cashproof/api"),
        ("apps/cli", root / "apps/cli/src/cashproof/cli"),
    ]

    missing = []
    for pkg_rel, src_pkg_dir in targets:
        pkg_root = root / pkg_rel
        pyproject = pkg_root / "pyproject.toml"
        init_py = src_pkg_dir / "__init__.py"
        py_typed = src_pkg_dir / "py.typed"

        if not pyproject.is_file():
            missing.append(str(pyproject.relative_to(root)))
        if not init_py.is_file():
            missing.append(str(init_py.relative_to(root)))
        if not py_typed.is_file():
            missing.append(str(py_typed.relative_to(root)))

    assert not missing, f"Missing package files: {missing}"


def test_gitignore_exists_and_covers_essentials() -> None:
    """Ensure .gitignore exists and ignores virtual environments, caches, and secrets."""
    root = get_project_root()
    gitignore_file = root / ".gitignore"
    assert gitignore_file.is_file(), ".gitignore must exist in project root"

    content = gitignore_file.read_text(encoding="utf-8")
    must_include = [".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".env"]
    missing = [entry for entry in must_include if entry not in content]
    assert not missing, f".gitignore missing essential entries: {missing}"
