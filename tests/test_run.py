"""Test simjsr.run."""

from copy import replace
from typing import Any

import pytest
from func_timeout import FunctionTimedOut

from simjsr import Config, run


def test__single(grimech_config: Config) -> None:
    """Test single simulation."""
    run.single(grimech_config)


def test__timeout(timeout_config: Config) -> None:
    """Test that a timeout error is raised when the simulation takes too long."""
    with pytest.raises(FunctionTimedOut):
        run.single(timeout_config)


@pytest.mark.parametrize(
    argnames=("arg_name", "arg_values"),
    argvalues=[
        ("pressure", [1, 10, 100]),
        ("temperature", [800, 900, 1000]),
        (
            "composition",
            [
                {"CH4": 0.05, "O2": 0.21, "N2": 0.74},
                {"CH4": 0.05, "O2": 0.22, "N2": 0.73},
                {"CH4": 0.05, "O2": 0.23, "N2": 0.72},
            ],
        ),
    ],
)
def test__multi(grimech_config: Config, arg_name: str, arg_values: list[Any]) -> None:
    """Test multi simulation."""
    configs = [replace(grimech_config, **{arg_name: v}) for v in arg_values]
    solns = run.multi(configs)
    assert len(solns) == len(arg_values)
