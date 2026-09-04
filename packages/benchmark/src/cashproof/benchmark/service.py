"""In-memory benchmark service for API and CLI integration.

Stores benchmark runs purely in memory (no database, no Redis, no Celery).
"""

from __future__ import annotations

from cashproof.application.ports import AIInvestigatorPort
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import BenchmarkRun
from cashproof.benchmark.runner import BenchmarkRunner
from cashproof.domain.ai import InvestigatorBudget


class InMemoryBenchmarkService:
    """In-memory registry and execution coordinator for benchmark runs."""

    def __init__(
        self,
        runner: BenchmarkRunner | None = None,
        investigator: AIInvestigatorPort | None = None,
        investigator_budget: InvestigatorBudget | None = None,
    ) -> None:
        self._runner = runner or BenchmarkRunner()
        self._investigator = investigator
        self._investigator_budget = investigator_budget
        self._runs: dict[str, BenchmarkRun] = {}

    def run_benchmark(
        self,
        seed: int = 42,
        num_settlements: int = 100,
        run_id: str | None = None,
        arm: str = "deterministic",
    ) -> BenchmarkRun:
        config = GeneratorConfig(seed=seed, num_settlements=num_settlements)
        active_investigator = self._investigator if arm == "ai_investigator" else None
        active_budget = self._investigator_budget if arm == "ai_investigator" else None

        run = self._runner.run(
            config=config,
            run_id=run_id,
            investigator=active_investigator,
            ai_budget=active_budget,
            arm=arm,
        )
        self._runs[run.run_id] = run
        return run

    def get_benchmark(self, run_id: str) -> BenchmarkRun | None:
        return self._runs.get(run_id)

    def list_benchmarks(self) -> list[BenchmarkRun]:
        return list(self._runs.values())
