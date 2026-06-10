"""Pytest configurations."""

from pathlib import Path

import pytest

from simjsr import Config


@pytest.fixture
def data_path(request: pytest.FixtureRequest) -> Path:
    """Path to test data."""
    return Path(request.path).parent / "data"


@pytest.fixture
def grimech_config(data_path: Path) -> Config:
    """Reference configuration for testing."""
    return Config(
        mech_file=data_path / "grimech3.0" / "chem.yaml",
        temperature=1000,
        pressure=1,
        residence_time=4,
        composition={"CH4": 0.05, "O2": 0.21, "N2": 0.74},
    )


@pytest.fixture
def slow_config(data_path: Path) -> Config:
    """Reference configuration for testing."""
    return Config(
        mech_file=data_path / "slow" / "chem.yaml",
        temperature=825,
        pressure=1.1,
        residence_time=4,
        composition={"CPT(563)": 0.005, "O2(6)": 0.133928571, "N2": 0.861071429},
        time_out=1,
    )
