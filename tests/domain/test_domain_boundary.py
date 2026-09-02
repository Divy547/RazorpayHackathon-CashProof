"""Domain package baseline boundary tests."""

import cashproof.domain


def test_domain_package_import() -> None:
    assert cashproof.domain.__version__ == "0.1.0"
