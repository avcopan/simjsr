"""Test simjsr.run."""

from copy import replace
from typing import Any

import pytest

from simjsr import solve
from simjsr.solve import Config


def test__single(grimech_config: Config) -> None:
    """Test single simulation."""
    solve.single(config=grimech_config)


def test__timeout(slow_config: Config) -> None:
    """Test that a timeout error is raised when the simulation takes too long."""
    with pytest.raises(TimeoutError):
        solve.single(config=slow_config)


@pytest.mark.parametrize(
    argnames=("arg_name", "arg_values"),
    argvalues=[
        ("pressure", [1, 10, 100]),
    ],
)
def test__multi(grimech_config: Config, arg_name: str, arg_values: list[Any]) -> None:
    """Test multi simulation."""
    configs = [replace(grimech_config, **{arg_name: v}) for v in arg_values]
    solns = solve.multi(configs=configs)
    assert len(solns) == len(arg_values)


def test__multi_temperature(grimech_config: Config) -> None:
    """Test multi-temperature simulation."""
    temperatures = [800, 900, 1000]
    solns = solve.multi_temperature(config=grimech_config, temperatures=temperatures)
    assert len(solns) == len(temperatures)


def test__multi_composition(grimech_config: Config) -> None:
    """Test multi-composition simulation."""
    compositions = [
        {"CH4": 0.05, "O2": 0.21, "N2": 0.74},
        {"CH4": 0.05, "O2": 0.22, "N2": 0.73},
        {"CH4": 0.05, "O2": 0.23, "N2": 0.72},
    ]
    solns = solve.multi_composition(config=grimech_config, compositions=compositions)
    assert len(solns) == len(compositions)
