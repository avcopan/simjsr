"""Test simjsr.run."""

from copy import replace
from pathlib import Path
from typing import Any

import pytest

from simjsr import solve
from simjsr.solve import Config


@pytest.fixture
def grimech_file(data_path: Path) -> Path:
    """Grimech 3.0 model."""
    return data_path / "grimech3.0" / "chem.yaml"


@pytest.fixture
def slowmech_file(data_path: Path) -> Path:
    """Slow model."""
    return data_path / "slow" / "chem.yaml"


@pytest.fixture
def grimech_config() -> Config:
    """Reference configuration for testing."""
    return Config(
        temperature=1000,
        pressure=1,
        residence_time=4,
        composition={"CH4": 0.05, "O2": 0.21, "N2": 0.74},
    )


@pytest.fixture
def slow_config() -> Config:
    """Reference configuration for testing."""
    return Config(
        temperature=825,
        pressure=1.1,
        residence_time=4,
        composition={"CPT(563)": 0.005, "O2(6)": 0.133928571, "N2": 0.861071429},
        time_out=1,
    )


def test__single(grimech_file: Path, grimech_config: Config) -> None:
    """Test single simulation."""
    solve.single(grimech_file, config=grimech_config)


def test__timeout(slowmech_file: Path, slow_config: Config) -> None:
    """Test that a timeout error is raised when the simulation takes too long."""
    with pytest.raises(TimeoutError):
        solve.single(slowmech_file, config=slow_config)


@pytest.mark.parametrize(
    argnames=("arg_name", "arg_values"),
    argvalues=[
        ("pressure", [1, 10, 100]),
    ],
)
def test__multi(
    grimech_file: Path, grimech_config: Config, arg_name: str, arg_values: list[Any]
) -> None:
    """Test multi simulation."""
    configs = [replace(grimech_config, **{arg_name: v}) for v in arg_values]
    solns = solve.multi(grimech_file, configs=configs)
    assert len(solns) == len(arg_values)


def test__multi_temperature(grimech_file: Path, grimech_config: Config) -> None:
    """Test multi-temperature simulation."""
    temperatures = [800, 900, 1000]
    solns = solve.multi_temperature(
        grimech_file, config=grimech_config, temperatures=temperatures
    )
    assert len(solns) == len(temperatures)


def test__multi_composition(grimech_file: Path, grimech_config: Config) -> None:
    """Test multi-composition simulation."""
    compositions = [
        {"CH4": 0.05, "O2": 0.21, "N2": 0.74},
        {"CH4": 0.05, "O2": 0.22, "N2": 0.73},
        {"CH4": 0.05, "O2": 0.23, "N2": 0.72},
    ]
    solns = solve.multi_composition(
        grimech_file, config=grimech_config, compositions=compositions
    )
    assert len(solns) == len(compositions)
