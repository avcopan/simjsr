"""Test simjsr.run."""

from pathlib import Path

import cantera as ct
import pytest

from simjsr import run
from simjsr.run import Config


@pytest.fixture
def grimech_model(data_path: Path) -> ct.Solution:
    """Grimech 3.0 model."""
    return ct.Solution(data_path / "grimech3.0/chem.yaml")


@pytest.fixture
def slow_model(data_path: Path) -> ct.Solution:
    """Slow model."""
    return ct.Solution(data_path / "slow/chem.yaml")


@pytest.fixture
def grimech_config() -> Config:
    """Reference configuration for testing."""
    return Config(
        temperature=1000,
        pressure=1,
        residence_time=4,
        concentrations={"CH4": 0.05, "O2": 0.21, "N2": 0.79},
    )


@pytest.fixture
def slow_config() -> Config:
    """Reference configuration for testing."""
    return Config(
        temperature=825,
        pressure=1.1,
        residence_time=4,
        concentrations={"CPT(563)": 0.005, "O2(6)": 0.133928571, "N2": 0.861071429},
        time_out=1,
    )


def test__single(grimech_model: ct.Solution, grimech_config: Config) -> None:
    """Stub test to ensure the test suite runs."""
    run.single(grimech_model, config=grimech_config)


def test__timeout(slow_model: ct.Solution, slow_config: Config) -> None:
    """Test that a timeout error is raised when the simulation takes too long."""
    with pytest.raises(TimeoutError):
        run.single(slow_model, config=slow_config)


def test__multi_temperature(grimech_model: ct.Solution, grimech_config: Config) -> None:
    """Stub test to ensure the test suite runs."""
    run.multi_temperature(
        grimech_model, config=grimech_config, temperatures=[900, 1000, 1100]
    )
