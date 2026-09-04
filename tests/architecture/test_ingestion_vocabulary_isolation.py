"""Phase 9: Razorpay/bank-CSV vocabulary must never leak into domain, application, or ai.

Complements test_import_boundaries.py (which checks imports) by checking for
literal source-specific vocabulary/id-shapes that could leak in even without
a forbidden import (e.g. a raw dict key access like dto["entity"], or a
literal "pay_xxx" id pattern). A prose mention of "Razorpay" inside a comment
or docstring (e.g. "implemented by RazorpayConnector", mirroring the existing
AIInvestigatorPort docstring's "e.g. cashproof.ai.AnthropicInvestigator") is
NOT itself a boundary violation - only literal DTO-shaped vocabulary is.

apps/api and apps/cli are composition roots and are explicitly allowed to
name concrete adapters (e.g. RazorpayConnector) when wiring them - only
domain/application/ai must stay ignorant of any one source's vocabulary.
"""

from __future__ import annotations

import re
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def find_python_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return [p for p in directory.rglob("*.py") if not p.name.startswith(".")]


FORBIDDEN_PATTERNS = [
    re.compile(r'"entity"\s*:'),
    re.compile(r"\bpay_[A-Za-z0-9]"),
    re.compile(r"\brfnd_[A-Za-z0-9]"),
    re.compile(r"\bsetl_[A-Za-z0-9]"),
]


def test_domain_application_and_ai_contain_no_razorpay_vocabulary() -> None:
    root = get_project_root()
    scanned_dirs = [
        root / "packages" / "domain" / "src",
        root / "packages" / "application" / "src",
        root / "packages" / "ai" / "src",
    ]

    violations: list[str] = []
    for scanned_dir in scanned_dirs:
        for file_path in find_python_files(scanned_dir):
            content = file_path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(content):
                    rel = file_path.relative_to(root)
                    violations.append(f"{rel} contains forbidden pattern {pattern.pattern!r}")

    assert not violations, "Razorpay vocabulary leaked into domain/application/ai:\n" + "\n".join(
        violations
    )
