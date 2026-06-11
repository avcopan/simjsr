"""CLI for running multi-temperature jet-stirred reactor simulations."""

import shutil
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from .config import Config, Key
from .run import multi

DATA_PATH = Path(__file__).parent / "data"

app = typer.Typer()


class File:
    """File names for example files."""

    chemkin = "chem.inp"
    cantera = "chem.yaml"
    temperature = "temperature.csv"
    composition = "composition.csv"
    config = "config.yaml"


class Format(StrEnum):
    """Input formats for chemical kinetic data."""

    chemkin = "chemkin"
    cantera = "cantera"


@app.command("run")
def run(
    config_file: Annotated[str, typer.Argument(help="Config file")] = File.config,
    *,
    output_file: Annotated[
        str, typer.Option("--output-file", "-o", help="File to save simulation results")
    ] = "output.csv",
    no_pass_state: Annotated[
        bool,
        typer.Option(
            "--no-pass-state", "-S", help="Turn off passing state between simulations"
        ),
    ] = False,
) -> None:
    """Run a JSR simulation workflow."""
    multi(
        config_file,
        pass_state=not no_pass_state,
        output_file=Path(output_file),
        logger=typer.echo,
    )


@app.command("example")
def example(
    directory: Annotated[
        str, typer.Argument(help="Directory to save example files.")
    ] = ".",
    *,
    format_: Annotated[
        Format,
        typer.Option("--format", "-f", help="Input format (chemkin or cantera)."),
    ] = Format.chemkin,
    multi_temperature: Annotated[
        bool,
        typer.Option(
            "--temperature", "-t", help="Prepare a multi-temperature simulation."
        ),
    ] = False,
    multi_composition: Annotated[
        bool,
        typer.Option(
            "--composition", "-c", help="Prepare a multi-composition simulation."
        ),
    ] = False,
) -> None:
    """Generate example config and input files."""
    dir_path = Path(directory)
    dir_path.mkdir(exist_ok=True)

    cantera_file = Path(File.cantera)
    chemkin_file = None
    if format_ == Format.chemkin:
        shutil.copy(DATA_PATH / File.chemkin, dir_path)
        chemkin_file = Path(File.chemkin)
    elif format_ == Format.cantera:
        shutil.copy(DATA_PATH / File.cantera, dir_path)

    temperature = 1000
    composition = {"CH4": 0.05, "O2": 0.21, "N2": 0.74}
    config = Config(
        cantera_file=cantera_file,
        temperature=temperature,
        pressure=1,
        residence_time=4,
        composition=composition,
        volume=1.0,
        time_out=None,
        chemkin_file=chemkin_file,
        chemkin_thermo_file=None,
    )
    update = {}

    if multi_temperature:
        temperature_file = dir_path / File.temperature
        data = {"Temperature (K)": [800, 900, 1000]}
        pl.DataFrame(data).write_csv(temperature_file)
        update[Key.temperature] = File.temperature

    if multi_composition:
        composition_file = dir_path / File.composition
        data = {
            "CH4": [0.05, 0.1, 0.15],
            "O2": [0.21, 0.21, 0.21],
            "N2": [0.74, 0.59, 0.44],
        }
        pl.DataFrame(data).write_csv(composition_file)
        update[Key.composition] = File.composition

    config.to_yaml(dir_path / File.config, update=update)
