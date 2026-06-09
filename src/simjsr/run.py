"""Reactors."""

import signal
from copy import replace
from dataclasses import dataclass
from pathlib import Path

import cantera as ct
from cantera import Solution, SolutionArray


@dataclass
class Config:
    """Configuration for a jet-stirred reactor simulation.

    Attributes:
        temperature: Temperature (K)
        pressure: Pressure (atm)
        residence_time: Residence time (s)
        volume: Volume (cm^3)
        concentrations: Starting concentrations
        time_out: Time limit for the simulation (s)
    """

    temperature: float
    pressure: float
    residence_time: float
    concentrations: dict[str, float]
    volume: float = 1.0
    time_out: int | None = None


def single(mech_file: str | Path, config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation.

    Args:
        mech_file: Mechanism file path
        config: Configuration for the simulation

    Returns:
        Steady state solution

    Raises:
        TimeoutError: If the simulation exceeds the configured time limit
    """
    # Set up a timeout handler to prevent simulations from running indefinitely
    if config.time_out is not None:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(config.time_out)

    try:
        result = _single(mech_file=mech_file, config=config)
    finally:
        signal.alarm(0)

    return result


def multi(
    mech_file: str | Path, configs: list[Config], *, chain: bool = True
) -> SolutionArray:
    """Run multiple jet-stirred reactor simulations.

    Args:
        mech_file: Mechanism file path
        configs: Configurations for the simulations
        chain: Whether to use the concentrations from the previous simulation as
            the starting point for the next simulation, if their initial
            concentrations match (default: True)

    Returns:
        Array of steady state solutions for each simulation
    """
    conc0 = None
    conc = None
    phase = ct.Solution(mech_file)
    results = SolutionArray(phase)
    for config0 in configs:
        # If requested, re-use solved concentrations
        config = config0
        if chain and config0.concentrations == conc0:
            config = replace(config0, concentrations=conc)

        result = single(mech_file=mech_file, config=config)
        results.append(result.state)

        conc0 = config0.concentrations
        conc = result.X
    return results


def _single(mech_file: str | Path, config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation (no timeout handling).

    Args:
        mech_file: Mechanism file path
        config: Configuration for the simulation

    Returns:
        Steady state solution
    """
    phase = ct.Solution(mech_file)

    # Use concentrations from the previous iteration to speed up convergence
    phase.TPX = config.temperature, config.pressure * ct.one_atm, config.concentrations

    # Set up JSR: inlet -> flow control -> reactor -> pressure control -> exhaust
    volume_m3 = config.volume * (1e-2) ** 3
    reactor = ct.IdealGasReactor(phase, energy="off", volume=volume_m3, clone=True)
    exhaust = ct.Reservoir(phase, clone=True)
    inlet = ct.Reservoir(phase, clone=True)
    ct.PressureController(
        upstream=reactor,
        downstream=exhaust,
        K=1e-3,
        primary=ct.MassFlowController(
            upstream=inlet,
            downstream=reactor,
            mdot=reactor.mass / config.residence_time,
        ),
    )
    reactor_net = ct.ReactorNet([reactor])
    reactor_net.advance_to_steady_state(max_steps=100000)
    return reactor.phase


def _timeout_handler(_signum: int, _frame: object) -> None:
    msg = "The simulation exceeded the configured time limit."
    raise TimeoutError(msg)
