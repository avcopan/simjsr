"""Test simjsr.run."""

from pathlib import Path

import cantera as ct
import pytest

from simjsr import run


@pytest.fixture
def grimech_model(data_path: Path) -> ct.Solution:
    """Grimech 3.0 model."""
    return ct.Solution(data_path / "grimech3.0/chem.yaml")


@pytest.fixture
def slow_model(data_path: Path) -> ct.Solution:
    """Slow model."""
    return ct.Solution(data_path / "slow/chem.yaml")


@pytest.mark.parametrize(
    argnames=("temperature", "pressure", "residence_time", "concentrations"),
    argvalues=[
        (1000, 1, 4, {"CH4": 0.05, "O2": 0.21, "N2": 0.79}),
    ],
)
def test__single(
    temperature: float,
    pressure: float,
    residence_time: float,
    concentrations: dict[str, float],
    grimech_model: ct.Solution,
) -> None:
    """Stub test to ensure the test suite runs."""
    config = run.Config(
        temperature=temperature,
        pressure=pressure,
        residence_time=residence_time,
        concentrations=concentrations,
    )
    run.single(model=grimech_model, config=config)


def test__timeout(slow_model: ct.Solution) -> None:
    """Test that a timeout error is raised when the simulation takes too long."""
    config = run.Config(
        temperature=825,
        pressure=1.1,
        residence_time=4,
        concentrations={"CPT(563)": 0.005, "O2(6)": 0.133928571, "N2": 0.861071429},
        time_out=1,
    )
    with pytest.raises(TimeoutError):
        run.single(model=slow_model, config=config)
