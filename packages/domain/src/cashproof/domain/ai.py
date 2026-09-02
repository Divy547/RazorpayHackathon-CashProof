"""CashProof AI Investigation Contracts and Strongly-Typed Budgets.

Defines immutable contracts for AI investigations and resolution proposals.
Contains zero framework/LLM SDK dependencies and supplies zero authoritative financial amounts.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cashproof.domain.derived import Evidence
from cashproof.domain.types import StopReason


@dataclass(frozen=True, slots=True)
class InvestigatorBudget:
    """Strongly-typed, immutable constraints on AI investigation resource consumption."""

    max_tool_calls: int
    max_tokens: int
    timeout_seconds: float
    temperature: float
    model_version: str

    def __post_init__(self) -> None:
        if self.max_tool_calls <= 0:
            raise ValueError(f"max_tool_calls must be positive, got {self.max_tool_calls}")
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        if (
            self.timeout_seconds <= 0.0
            or math.isnan(self.timeout_seconds)
            or math.isinf(self.timeout_seconds)
        ):
            raise ValueError(
                f"timeout_seconds must be a positive finite float, got {self.timeout_seconds}"
            )
        if (
            math.isnan(self.temperature)
            or math.isinf(self.temperature)
            or not (0.0 <= self.temperature <= 1.0)
        ):
            raise ValueError(f"temperature must be between 0.0 and 1.0, got {self.temperature}")
        if not self.model_version.strip():
            raise ValueError("model_version must not be empty.")


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    """Immutable audit record of a single tool invocation during investigation."""

    tool_name: str
    arguments: tuple[tuple[str, str], ...]
    response_summary: str
    duration_ms: int

    def __init__(
        self,
        tool_name: str,
        arguments: Mapping[str, str] | Iterable[tuple[str, str]],
        response_summary: str,
        duration_ms: int,
    ) -> None:
        if not tool_name.strip():
            raise ValueError("tool_name must not be empty.")
        if duration_ms < 0:
            raise ValueError(f"duration_ms must be non-negative, got {duration_ms}")

        if isinstance(arguments, Mapping):
            frozen_args = tuple(sorted((str(k), str(v)) for k, v in arguments.items()))
        else:
            frozen_args = tuple((str(k), str(v)) for k, v in arguments)

        object.__setattr__(self, "tool_name", tool_name)
        object.__setattr__(self, "arguments", frozen_args)
        object.__setattr__(self, "response_summary", response_summary)
        object.__setattr__(self, "duration_ms", duration_ms)


@dataclass(frozen=True, slots=True)
class Investigation:
    """Immutable record of an AI investigation session."""

    investigation_id: str
    case_id: str
    run_id: str
    budget: InvestigatorBudget
    tool_calls: tuple[ToolCallRecord, ...]
    stop_reason: StopReason
    candidates_considered: tuple[str, ...]

    def __init__(
        self,
        investigation_id: str,
        case_id: str,
        run_id: str,
        budget: InvestigatorBudget,
        tool_calls: Iterable[ToolCallRecord],
        stop_reason: StopReason,
        candidates_considered: Iterable[str],
    ) -> None:
        if not investigation_id.strip():
            raise ValueError("investigation_id must not be empty.")
        if not case_id.strip():
            raise ValueError("case_id must not be empty.")
        if not run_id.strip():
            raise ValueError("run_id must not be empty.")

        object.__setattr__(self, "investigation_id", investigation_id)
        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "budget", budget)
        object.__setattr__(self, "tool_calls", tuple(tool_calls))
        object.__setattr__(self, "stop_reason", stop_reason)
        object.__setattr__(self, "candidates_considered", tuple(candidates_considered))


@dataclass(frozen=True, slots=True)
class ResolutionProposal:
    """Immutable hypothesis proposed by AI investigation.

    References target records only; provides zero authoritative financial amounts.
    Confidence is purely descriptive and never authorizes automatic resolution.
    """

    proposal_id: str
    investigation_id: str
    case_id: str
    run_id: str
    target_ledger_entry_ids: frozenset[str]
    rationale: str
    evidence: tuple[Evidence, ...]
    confidence: float

    def __init__(
        self,
        proposal_id: str,
        investigation_id: str,
        case_id: str,
        run_id: str,
        target_ledger_entry_ids: Iterable[str],
        rationale: str,
        evidence: Iterable[Evidence],
        confidence: float,
    ) -> None:
        if not proposal_id.strip():
            raise ValueError("proposal_id must not be empty.")
        if not investigation_id.strip():
            raise ValueError("investigation_id must not be empty.")
        if not case_id.strip():
            raise ValueError("case_id must not be empty.")
        if not run_id.strip():
            raise ValueError("run_id must not be empty.")
        if math.isnan(confidence) or math.isinf(confidence):
            raise ValueError("confidence must be a finite float.")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        object.__setattr__(self, "proposal_id", proposal_id)
        object.__setattr__(self, "investigation_id", investigation_id)
        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "target_ledger_entry_ids", frozenset(target_ledger_entry_ids))
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(self, "evidence", tuple(evidence))
        object.__setattr__(self, "confidence", float(confidence))
