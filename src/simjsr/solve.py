"""Reactors."""

import signal
from collections.abc import Mapping, Sequence
from copy import replace
from dataclasses import dataclass
from pathlib import Path

import cantera as ct
from cantera import Solution


@dataclass
class Config:
    """Configuration for a jet-stirred reactor simulation.

    Attributes:
        mech_file: Mechanism file path
        temperature: Temperature (K)
        pressure: Pressure (atm)
        residence_time: Residence time (s)
        volume: Volume (cm^3)
        composition: Starting composition (mole fractions)
        time_out: Time limit for the simulation (s)
    """

    mech_file: Path
    temperature: float
    pressure: float
    residence_time: float
    composition: dict[str, float]
    volume: float = 1.0
    time_out: int | None = None

    def is_compatible_with(self, other: "Config | None") -> bool:
        """Check if this config is compatible with another config for chaining."""
        if other is None:
            return False
        return (
            self.mech_file == other.mech_file and self.composition == other.composition
        )


def single(config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation.

    Args:
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
        soln = _single(config=config)
    finally:
        signal.alarm(0)

    return soln


def multi(configs: Sequence[Config], *, chain: bool = True) -> list[Solution]:
    """Run multiple jet-stirred reactor simulations.

    Args:
        configs: Configurations for the simulations
        chain: Whether to use the composition from the previous simulation as
            the starting point for the next simulation, if their initial
            composition match (default: True)

    Returns:
        Array of steady state solutions for each simulation
    """
    last_config = last_soln = None
    solns = []
    for init_config in configs:
        # If requested, re-use solved composition
        config = init_config
        if (
            chain
            and init_config.is_compatible_with(last_config)
            and last_soln is not None
        ):
            config = replace(init_config, composition=last_soln.X)

        soln = single(config=config)
        solns.append(soln)

        last_config = init_config
        last_soln = soln

    return solns


def multi_temperature(config: Config, temperatures: Sequence[float]) -> list[Solution]:
    """Run multiple jet-stirred reactor simulations at different temperatures.

    Args:
        config: Base configuration for the simulations
        temperatures: List of temperatures (K)

    Returns:
        Array of steady state solutions for each simulation
    """
    configs = [replace(config, temperature=t) for t in temperatures]
    return multi(configs)


def multi_composition(
    config: Config, compositions: Sequence[Mapping[str, float]]
) -> list[Solution]:
    """Run multiple jet-stirred reactor simulations at different compositions.

    Args:
        config: Base configuration for the simulations
        compositions: List of compositions (mole fractions)

    Returns:
        Array of steady state solutions for each simulation
    """
    configs = [replace(config, composition=comp) for comp in compositions]
    return multi(configs)


def _single(config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation (no timeout handling).

    Args:
        config: Configuration for the simulation

    Returns:
        Steady state solution
    """
    phase = ct.Solution(config.mech_file)

    # Use composition from the previous iteration to speed up convergence
    phase.TPX = config.temperature, config.pressure * ct.one_atm, config.composition

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
