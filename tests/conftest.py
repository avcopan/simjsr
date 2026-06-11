"""Pytest configurations."""

from pathlib import Path

import pytest

from simjsr import Config


@pytest.fixture
def data_path(request: pytest.FixtureRequest) -> Path:
    """Path to test data."""
    return Path(request.path).parent / "data"


@pytest.fixture
def examples_path(request: pytest.FixtureRequest) -> Path:
    """Path to examples."""
    return Path(request.path).parents[1] / "examples"


@pytest.fixture
def grimech_config_single_path(data_path: Path) -> Path:
    """Reference configuration path for testing."""
    return data_path / "grimech3.0" / "config_single.yaml"


@pytest.fixture
def grimech_config_multi_temperature_path(data_path: Path) -> Path:
    """Reference configuration path for testing."""
    return data_path / "grimech3.0" / "config_multi_temperature.yaml"


@pytest.fixture
def grimech_config_multi_composition_path(data_path: Path) -> Path:
    """Reference configuration path for testing."""
    return data_path / "grimech3.0" / "config_multi_composition.yaml"


@pytest.fixture
def grimech_config(data_path: Path) -> Config:
    """Reference configuration for testing."""
    return Config(
        cantera_file=data_path / "grimech3.0" / "chem.yaml",
        temperature=1000,
        pressure=1,
        residence_time=4,
        composition={"CH4": 0.05, "O2": 0.21, "N2": 0.74},
    )


@pytest.fixture
def timeout_config(data_path: Path) -> Config:
    """Reference configuration for testing."""
    return Config(
        cantera_file=data_path / "grimech3.0" / "chem.yaml",
        temperature=1000,
        pressure=1,
        residence_time=4,
        composition={"CH4": 0.05, "O2": 0.21, "N2": 0.74},
        time_out=0.0000001,
    )
