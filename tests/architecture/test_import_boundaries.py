"""Architecture and import boundary tests.

Enforces:
1. domain must not import application, infrastructure, ai, benchmark, FastAPI, SQLAlchemy,
   Anthropic SDK, Pydantic, or frontend.
2. application must not import infrastructure or concrete AI implementations.
3. ai must not import infrastructure or benchmark.
4. infrastructure must not import ai or benchmark.
5. apps/api and apps/cli are composition/adapter roots.
6. production code must not import benchmark.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import NamedTuple


class ImportRecord(NamedTuple):
    file_path: Path
    module_name: str
    line_number: int


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def extract_imports(file_path: Path) -> list[ImportRecord]:
    """Parse a python source file and return all imported module names."""
    content = file_path.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(file_path))
    records: list[ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                records.append(
                    ImportRecord(
                        file_path=file_path,
                        module_name=alias.name,
                        line_number=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                records.append(
                    ImportRecord(
                        file_path=file_path,
                        module_name=node.module,
                        line_number=node.lineno,
                    )
                )
    return records


def find_python_files(directory: Path) -> list[Path]:
    """Find all .py files in a directory recursively."""
    if not directory.exists():
        return []
    return [p for p in directory.rglob("*.py") if not p.name.startswith(".")]


def is_forbidden_import(imported_module: str, forbidden_prefixes: list[str]) -> bool:
    """Check if an imported module matches any forbidden prefix."""
    for prefix in forbidden_prefixes:
        if imported_module == prefix or imported_module.startswith(prefix + "."):
            return True
    return False


def test_domain_import_boundaries() -> None:
    """Domain layer must have zero dependencies on frameworks, databases, or other layers."""
    root = get_project_root()
    domain_dir = root / "packages" / "domain" / "src"
    py_files = find_python_files(domain_dir)
    assert len(py_files) > 0, "No Python files found in packages/domain/src"

    forbidden = [
        # Internal layers
        "cashproof.application",
        "cashproof.infrastructure",
        "cashproof.ai",
        "cashproof.benchmark",
        "cashproof.api",
        "cashproof.cli",
        "application",
        "infrastructure",
        "ai",
        "benchmark",
        "apps",
        "frontend",
        # Frameworks / HTTP / DB / LLM / External libraries
        "fastapi",
        "starlette",
        "sqlalchemy",
        "alembic",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "anthropic",
        "openai",
        "pydantic",
        "requests",
        "httpx",
        "aiohttp",
        "celery",
        "redis",
        "kafka",
        "confluent_kafka",
        "langchain",
        "crewai",
        "autogen",
        "llamaindex",
        "neo4j",
    ]

    violations: list[str] = []
    for file_path in py_files:
        imports = extract_imports(file_path)
        for record in imports:
            if is_forbidden_import(record.module_name, forbidden):
                rel = record.file_path.relative_to(root)
                violations.append(
                    f"{rel}:{record.line_number} imports forbidden module '{record.module_name}'"
                )

    assert not violations, "Domain import boundary violations:\n" + "\n".join(violations)


def test_application_import_boundaries() -> None:
    """Application layer defines ports, but must NOT import infrastructure or concrete AI."""
    root = get_project_root()
    app_dir = root / "packages" / "application" / "src"
    py_files = find_python_files(app_dir)
    assert len(py_files) > 0, "No Python files found in packages/application/src"

    forbidden = [
        # Internal concrete adapter layers
        "cashproof.infrastructure",
        "cashproof.ai",
        "cashproof.benchmark",
        "cashproof.api",
        "cashproof.cli",
        "infrastructure",
        "ai",
        "benchmark",
        "apps",
        "frontend",
        # Heavy frameworks & drivers
        "fastapi",
        "starlette",
        "sqlalchemy",
        "alembic",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "anthropic",
        "openai",
        "celery",
        "redis",
        "kafka",
        "confluent_kafka",
        "langchain",
        "crewai",
        "autogen",
        "llamaindex",
    ]

    violations: list[str] = []
    for file_path in py_files:
        imports = extract_imports(file_path)
        for record in imports:
            if is_forbidden_import(record.module_name, forbidden):
                rel = record.file_path.relative_to(root)
                violations.append(
                    f"{rel}:{record.line_number} imports forbidden module '{record.module_name}'"
                )

    assert not violations, "Application import boundary violations:\n" + "\n".join(violations)


def test_ai_import_boundaries() -> None:
    """AI layer implements application AI ports, but must NOT import infrastructure or benchmark."""
    root = get_project_root()
    ai_dir = root / "packages" / "ai" / "src"
    py_files = find_python_files(ai_dir)
    assert len(py_files) > 0, "No Python files found in packages/ai/src"

    forbidden = [
        "cashproof.infrastructure",
        "cashproof.benchmark",
        "cashproof.api",
        "cashproof.cli",
        "infrastructure",
        "benchmark",
        "apps",
        "frontend",
        "celery",
        "redis",
        "kafka",
        "confluent_kafka",
        "langchain",
        "crewai",
        "autogen",
        "llamaindex",
    ]

    violations: list[str] = []
    for file_path in py_files:
        imports = extract_imports(file_path)
        for record in imports:
            if is_forbidden_import(record.module_name, forbidden):
                rel = record.file_path.relative_to(root)
                violations.append(
                    f"{rel}:{record.line_number} imports forbidden module '{record.module_name}'"
                )

    assert not violations, "AI import boundary violations:\n" + "\n".join(violations)


def test_infrastructure_import_boundaries() -> None:
    """Infrastructure layer must NOT import concrete AI, benchmark, or apps."""
    root = get_project_root()
    infra_dir = root / "packages" / "infrastructure" / "src"
    py_files = find_python_files(infra_dir)
    assert len(py_files) > 0, "No Python files found in packages/infrastructure/src"

    forbidden = [
        "cashproof.ai",
        "cashproof.benchmark",
        "cashproof.api",
        "cashproof.cli",
        "ai",
        "benchmark",
        "apps",
        "frontend",
        "celery",
        "redis",
        "kafka",
        "confluent_kafka",
        "langchain",
        "crewai",
        "autogen",
        "llamaindex",
    ]

    violations: list[str] = []
    for file_path in py_files:
        imports = extract_imports(file_path)
        for record in imports:
            if is_forbidden_import(record.module_name, forbidden):
                rel = record.file_path.relative_to(root)
                violations.append(
                    f"{rel}:{record.line_number} imports forbidden module '{record.module_name}'"
                )

    assert not violations, "Infrastructure import boundary violations:\n" + "\n".join(violations)


def test_production_code_does_not_import_benchmark() -> None:
    """Production packages must never import benchmark."""
    root = get_project_root()
    prod_dirs = [
        root / "packages" / "domain" / "src",
        root / "packages" / "application" / "src",
        root / "packages" / "infrastructure" / "src",
        root / "packages" / "ai" / "src",
        root / "apps" / "api" / "src",
    ]

    forbidden = [
        "cashproof.benchmark",
        "benchmark",
    ]

    violations: list[str] = []
    for prod_dir in prod_dirs:
        for file_path in find_python_files(prod_dir):
            imports = extract_imports(file_path)
            for record in imports:
                if is_forbidden_import(record.module_name, forbidden):
                    rel = record.file_path.relative_to(root)
                    violations.append(
                        f"{rel}:{record.line_number} imports "
                        f"forbidden module '{record.module_name}'"
                    )

    assert not violations, "Production code importing benchmark:\n" + "\n".join(violations)


def test_import_boundary_scanner_detects_violations() -> None:
    """Self-verification: Ensure AST boundary scanner correctly catches prohibited imports."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("import sqlalchemy\nfrom cashproof.infrastructure import db\n")
        temp_path = Path(f.name)

    try:
        imports = extract_imports(temp_path)
        modules = [r.module_name for r in imports]
        assert "sqlalchemy" in modules
        assert "cashproof.infrastructure" in modules
        assert is_forbidden_import("sqlalchemy", ["sqlalchemy"])
        assert is_forbidden_import("cashproof.infrastructure", ["cashproof.infrastructure"])
        assert not is_forbidden_import("cashproof.domain", ["cashproof.infrastructure"])
    finally:
        temp_path.unlink()
