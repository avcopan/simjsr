"""Test simjsr.run."""

from pathlib import Path

import cantera as ct
import pytest

from simjsr import run


@pytest.fixture
def grimech_model(data_path: Path) -> ct.Solution:
    """Grimech 3.0 model."""
    return ct.Solution(data_path / "grimech3.0/chem.yaml")


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
