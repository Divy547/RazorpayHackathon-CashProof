"""Isolated deterministic pseudo-random number generator for synthetic data."""

from __future__ import annotations

import random
from collections.abc import Sequence


class DeterministicRNG:
    """Isolated PRNG wrapper ensuring deterministic generation."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def integer(self, min_val: int, max_val: int) -> int:
        return self._rng.randint(min_val, max_val)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def choice[T](self, seq: Sequence[T]) -> T:
        return self._rng.choice(seq)

    def sample[T](self, population: Sequence[T], k: int) -> list[T]:
        return self._rng.sample(population, k)

    def shuffle[T](self, x: list[T]) -> None:
        self._rng.shuffle(x)

    def hex_id(self, prefix: str, length: int = 12) -> str:
        """Generates a uniform lowercase hex string ID with a standard prefix."""
        val = self._rng.getrandbits(length * 4)
        return f"{prefix}_{val:0{length}x}"
