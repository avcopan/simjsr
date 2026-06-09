"""simjsr tests."""

import simjsr


def test_stub() -> None:
    """Stub test to ensure the test suite runs."""
    print(simjsr.__version__)  # noqa: T201


def test__greet() -> None:
    """Test the greet function."""
    assert simjsr.greet("World") == "Hello, World!"


def test__greet_jim() -> None:
    """Test the greet_jim function."""
    assert simjsr.greet_jim() == "Hello, Jim!"
