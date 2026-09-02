"""Application package baseline boundary tests."""

import cashproof.application


def test_application_package_import() -> None:
    assert cashproof.application.__version__ == "0.1.0"
