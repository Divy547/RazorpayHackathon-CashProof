"""Infrastructure package baseline boundary tests."""

import cashproof.infrastructure


def test_infrastructure_package_import() -> None:
    assert cashproof.infrastructure.__version__ == "0.1.0"
