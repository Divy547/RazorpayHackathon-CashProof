"""Tests enforcing forbidden dependencies and minimal dependency architecture.

Rules enforced:
- Zero distributed/unnecessary frameworks (Celery, Redis, Kafka, Kubernetes, LangChain, etc.).
- packages/domain has 0 external runtime dependencies.
- packages/application depends only on domain.
- packages/ai does not depend on infrastructure or benchmark.
- packages/infrastructure does not depend on ai or benchmark.
- Production packages do not depend on benchmark.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_toml(path: Path) -> dict[str, object]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


FORBIDDEN_DEPENDENCIES = {
    "celery",
    "redis",
    "kafka",
    "confluent-kafka",
    "aiokafka",
    "kubernetes",
    "langchain",
    "langchain-core",
    "langchain-community",
    "crewai",
    "autogen",
    "autogen-agentchat",
    "llama-index",
    "llamaindex",
    "neo4j",
    "networkx",
}


def _clean_dep_name(dep: str) -> str:
    for sep in [">=", "==", "<=", "~=", "[", "@"]:
        dep = dep.split(sep)[0]
    return dep.strip().lower()


def test_no_forbidden_dependencies_in_any_pyproject() -> None:
    """Ensure no pyproject.toml in the workspace lists forbidden packages."""
    root = get_project_root()
    pyproject_files = [p for p in root.rglob("pyproject.toml") if ".venv" not in p.parts]

    assert len(pyproject_files) >= 8, (
        f"Expected at least 8 pyproject.toml files, found {len(pyproject_files)}"
    )

    violations: list[str] = []
    for p in pyproject_files:
        data = load_toml(p)
        project_data = data.get("project", {})
        if isinstance(project_data, dict):
            dependencies = project_data.get("dependencies", [])
            if isinstance(dependencies, list):
                for dep in dependencies:
                    if _clean_dep_name(str(dep)) in FORBIDDEN_DEPENDENCIES:
                        violations.append(
                            f"{p.relative_to(root)} declares forbidden dependency '{dep}'"
                        )

        dep_groups = data.get("dependency-groups", {})
        if isinstance(dep_groups, dict):
            for group_name, group_deps in dep_groups.items():
                if isinstance(group_deps, list):
                    for dep in group_deps:
                        if _clean_dep_name(str(dep)) in FORBIDDEN_DEPENDENCIES:
                            violations.append(
                                f"{p.relative_to(root)} [dependency-groups.{group_name}] "
                                f"declares forbidden dependency '{dep}'"
                            )

    assert not violations, "Forbidden dependencies found:\n" + "\n".join(violations)


def test_domain_pyproject_has_zero_dependencies() -> None:
    """packages/domain must have 0 external runtime dependencies."""
    root = get_project_root()
    domain_toml = load_toml(root / "packages" / "domain" / "pyproject.toml")
    project_data = domain_toml.get("project", {})
    assert isinstance(project_data, dict)
    deps = project_data.get("dependencies", [])
    assert deps == [], f"Domain package must have no runtime dependencies, found: {deps}"


def test_application_pyproject_dependencies() -> None:
    """packages/application may depend on domain, but never on infrastructure or concrete AI."""
    root = get_project_root()
    app_toml = load_toml(root / "packages" / "application" / "pyproject.toml")
    project_data = app_toml.get("project", {})
    assert isinstance(project_data, dict)
    deps = project_data.get("dependencies", [])
    assert isinstance(deps, list)
    for dep in deps:
        dep_str = str(dep).lower()
        assert "infrastructure" not in dep_str, (
            f"Application declared infrastructure dependency: {dep_str}"
        )
        assert "cashproof-ai" not in dep_str and dep_str.strip() != "ai", (
            f"Application declared concrete AI dependency: {dep_str}"
        )
        assert "benchmark" not in dep_str, f"Application declared benchmark dependency: {dep_str}"


def test_ai_pyproject_dependencies() -> None:
    """packages/ai must not declare dependencies on infrastructure or benchmark."""
    root = get_project_root()
    ai_toml = load_toml(root / "packages" / "ai" / "pyproject.toml")
    project_data = ai_toml.get("project", {})
    assert isinstance(project_data, dict)
    deps = project_data.get("dependencies", [])
    assert isinstance(deps, list)
    for dep in deps:
        dep_str = str(dep).lower()
        assert "infrastructure" not in dep_str, f"AI declared infrastructure dependency: {dep_str}"
        assert "benchmark" not in dep_str, f"AI declared benchmark dependency: {dep_str}"


def test_infrastructure_pyproject_dependencies() -> None:
    """packages/infrastructure must not declare dependencies on ai or benchmark."""
    root = get_project_root()
    infra_toml = load_toml(root / "packages" / "infrastructure" / "pyproject.toml")
    project_data = infra_toml.get("project", {})
    assert isinstance(project_data, dict)
    deps = project_data.get("dependencies", [])
    assert isinstance(deps, list)
    for dep in deps:
        dep_str = str(dep).lower()
        assert "cashproof-ai" not in dep_str and dep_str.strip() != "ai", (
            f"Infrastructure declared AI dependency: {dep_str}"
        )
        assert "benchmark" not in dep_str, (
            f"Infrastructure declared benchmark dependency: {dep_str}"
        )


def test_api_pyproject_does_not_depend_on_benchmark() -> None:
    """apps/api must not declare dependency on benchmark."""
    root = get_project_root()
    api_toml = load_toml(root / "apps" / "api" / "pyproject.toml")
    project_data = api_toml.get("project", {})
    assert isinstance(project_data, dict)
    deps = project_data.get("dependencies", [])
    assert isinstance(deps, list)
    for dep in deps:
        dep_str = str(dep).lower()
        assert "benchmark" not in dep_str, f"API declared benchmark dependency: {dep_str}"
