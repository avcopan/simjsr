"""Reactors."""

import signal
from copy import replace
from dataclasses import dataclass

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


def single(model: Solution, config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation.

    Args:
        model: Chemical kinetics model
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
        result = _single(model=model, config=config)
    finally:
        signal.alarm(0)

    return result


def multi(
    model: Solution, configs: list[Config], *, chain: bool = True
) -> SolutionArray:
    """Run multiple jet-stirred reactor simulations.

    Args:
        model: Chemical kinetics model
        configs: Configurations for the simulations
        chain: Whether to use the concentrations from the previous simulation as
            the starting point for the next simulation, if their initial
            concentrations match (default: True)

    Returns:
        Array of steady state solutions for each simulation
    """
    conc0 = None
    conc = None
    results = SolutionArray(model)
    for config0 in configs:
        # If requested, re-use solved concentrations
        config = config0
        if chain and config0.concentrations == conc0:
            config = replace(config0, concentrations=conc)

        result = single(model=model, config=config)
        results.append(result.state)

        conc0 = config0.concentrations
        conc = result.X
    return results


def multi_temperature(
    model: Solution, config: Config, temperatures: list[float]
) -> SolutionArray:
    """Run multiple jet-stirred reactor simulations at different temperatures.

    Args:
        model: Chemical kinetics model
        config: Configuration for the simulations (except temperature)
        temperatures: Temperatures to simulate (K)

    Returns:
        Array of steady state solutions for each simulation
    """
    configs = [replace(config, temperature=T) for T in temperatures]
    return multi(model=model, configs=configs, chain=True)


def _single(model: Solution, config: Config) -> Solution:
    """Run a single jet-stirred reactor simulation (no timeout handling).

    Args:
        model: Chemical kinetics model
        config: Configuration for the simulation

    Returns:
        Steady state solution
    """
    # Use concentrations from the previous iteration to speed up convergence
    model.TPX = config.temperature, config.pressure * ct.one_atm, config.concentrations

    # Set up JSR: inlet -> flow control -> reactor -> pressure control -> exhaust
    volume_m3 = config.volume * (1e-2) ** 3
    reactor = ct.IdealGasReactor(model, energy="off", volume=volume_m3, clone=True)
    exhaust = ct.Reservoir(model, clone=True)
    inlet = ct.Reservoir(model, clone=True)
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
