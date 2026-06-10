"""Reactors."""

import signal
from collections.abc import Mapping, Sequence
from copy import replace

import cantera as ct
from cantera import Solution

from .config import Config


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
    phase = ct.Solution(config.cantera_file)

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
