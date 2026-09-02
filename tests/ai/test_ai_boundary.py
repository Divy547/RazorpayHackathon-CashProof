"""AI package baseline boundary tests."""

import cashproof.ai


def test_ai_package_import() -> None:
    assert cashproof.ai.__version__ == "0.1.0"
