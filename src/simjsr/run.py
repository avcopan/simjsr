"""Reactors."""

from dataclasses import dataclass

import cantera as ct
from cantera import Reactor, Solution


@dataclass
class Config:
    """Configuration for a jet-stirred reactor simulation.

    Attributes:
        temperature: Temperature (K)
        pressure: Pressure (atm)
        residence_time: Residence time (s)
        volume: Volume (cm^3)
        concentrations: Starting concentrations
    """

    temperature: float
    pressure: float
    residence_time: float
    concentrations: dict[str, float]
    volume: float = 1.0


def single(model: Solution, config: Config) -> Reactor:
    """Run a single jet-stirred reactor simulation.

    Args:
        model: Chemical kinetics model
        config: Configuration for the simulation

    Returns:
        Reactor at steady state
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
    return reactor
