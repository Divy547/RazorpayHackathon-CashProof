"""Benchmark package baseline boundary tests."""

import cashproof.benchmark


def test_benchmark_package_import() -> None:
    assert cashproof.benchmark.__version__ == "0.1.0"
