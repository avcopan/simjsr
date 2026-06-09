"""Pytest configurations."""

from pathlib import Path

import pytest


@pytest.fixture
def data_path(request: pytest.FixtureRequest) -> Path:
    """Path to test data."""
    return Path(request.path).parent / "data"
