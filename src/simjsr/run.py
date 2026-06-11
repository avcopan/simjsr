"""Reactors."""

import textwrap
from collections.abc import Callable, Mapping, Sequence
from copy import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any

import cantera as ct
import polars as pl
from func_timeout import FunctionTimedOut, func_timeout

from . import convert
from .config import Config

Logger = Callable[[str], Any]


def single(
    config: Config,
    *,
    logger: Logger | None = None,
    output_file: Path | None = None,
    raise_on_timout: bool = True,
) -> dict[str, float]:
    """Run a single jet-stirred reactor simulation.

    Args:
        config: Configuration for the simulation
        logger: Optional logger for messages
        output_file: Optional file to save simulation results
        raise_on_timout: Whether to raise a TimeoutError if the simulation times out

    Returns:
        Steady state mole fractions

    Raises:
        TimeoutError: If the simulation exceeds the configured time limit
    """
    start_counter = clock_start(logger, "Starting simulation")

    if not config.cantera_file.exists():
        generate_cantera_file_from_chemkin(config, logger=logger)

    phase = ct.Solution(config.cantera_file)

    try:
        mole_fracs = (
            _single(config)
            if config.time_out is None
            else func_timeout(config.time_out, _single, (config,))
        )
    except FunctionTimedOut:
        clock_end(logger, "Simulation timed out", start_counter)
        mole_fracs = {s: float("nan") for s in phase.species_names}
        if raise_on_timout:
            raise
    else:
        clock_end(logger, "Finished simulation", start_counter)

    if output_file is not None:
        pl.from_dicts([mole_fracs]).write_csv(output_file)

    return mole_fracs


def multi(
    configs: Sequence[Config],
    *,
    pass_state: bool = True,
    output_file: Path | None = None,
    logger: Logger | None = None,
) -> list[dict[str, float]]:
    """Run multiple jet-stirred reactor simulations.

    Args:
        configs: Configurations for the simulations
        pass_state: Whether to pass solved state to the next simulation, if its
            initial composition is the same
        logger: Optional logger for messages
        output_file: Optional file to save simulation results

    Returns:
        Steady state mole fractions for each simulation
    """
    config_count = len(configs)
    last_config = last_mole_fracs = None
    mole_fracs_lst = []
    for num, init_config in enumerate(configs, start=1):
        if logger is not None:
            yaml_text = init_config.yaml_text(describe=True)
            logger(f"Run {num} / {config_count}:")
            logger(textwrap.indent(yaml_text.strip(), "  "))

        # If requested, re-use solved composition
        config = init_config
        if (
            pass_state
            and init_config.is_compatible_with(last_config)
            and last_mole_fracs is not None
        ):
            config = replace(init_config, composition=last_mole_fracs)

        mole_fracs = single(config=config, logger=logger, raise_on_timout=False)
        mole_fracs_lst.append(mole_fracs)

        last_config = init_config
        last_mole_fracs = mole_fracs

        if logger is not None and num < config_count:
            logger("")

    if output_file is not None:
        pl.from_dicts(mole_fracs_lst).write_csv(output_file)

    return mole_fracs_lst


def multi_temperature(
    config: Config, temperatures: Sequence[float], *, logger: Logger | None = None
) -> list[dict[str, float]]:
    """Run multiple jet-stirred reactor simulations at different temperatures.

    Args:
        config: Base configuration for the simulations
        temperatures: List of temperatures (K)
        logger: Optional logger for messages

    Returns:
        Steady state mole fractions for each simulation
    """
    configs = [replace(config, temperature=t) for t in temperatures]
    return multi(configs, logger=logger)


def multi_composition(
    config: Config,
    compositions: Sequence[Mapping[str, float]],
    *,
    logger: Logger | None = None,
) -> list[dict[str, float]]:
    """Run multiple jet-stirred reactor simulations at different compositions.

    Args:
        config: Base configuration for the simulations
        compositions: List of compositions (mole fractions)
        logger: Optional logger for messages

    Returns:
        Steady state mole fractions for each simulation
    """
    configs = [replace(config, composition=comp) for comp in compositions]
    return multi(configs, logger=logger)


def _single(config: Config) -> dict[str, float]:
    """Run a single jet-stirred reactor simulation (no timeout handling or logging).

    Args:
        config: Configuration for the simulation

    Returns:
        Steady state mole fractions
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
    return reactor.phase.mole_fraction_dict()


# Helpers
def generate_cantera_file_from_chemkin(
    config: Config, *, logger: Logger | None = None
) -> None:
    """Ensure the Cantera file is available."""
    if config.chemkin_file is None:
        msg = "chemkin_file must be provided if cantera_file does not exist."
        raise ValueError(msg)

    if not config.chemkin_file.exists():
        msg = f"{config.chemkin_file = } does not exist."
        raise ValueError(msg)

    if logger is not None:
        logger(
            f"Converting {config.chemkin_file} to Cantera format "
            f"({config.cantera_file})"
        )

    convert.from_chemkin(
        chemkin_file=config.chemkin_file,
        chemkin_thermo_file=config.chemkin_thermo_file,
        cantera_file=config.cantera_file,
    )


def clock_start(logger: Logger | None, event: str) -> float:
    """Log the start time of an event."""
    if logger is not None:
        start_time = datetime.now(tz=UTC)
        logger(f"{event} at {start_time:%Y-%m-%d %H:%M:%S}")
    return perf_counter()


def clock_end(logger: Logger | None, event: str, start_counter: float) -> None:
    """Log the start time of a simulation."""
    if logger is not None:
        end_time = datetime.now(tz=UTC)
        elapsed = timedelta(seconds=perf_counter() - start_counter)
        logger(f"{event} at {end_time:%Y-%m-%d %H:%M:%S}")
        logger(f"Elapsed time: {elapsed}")
