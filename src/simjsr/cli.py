"""CLI for running multi-temperature jet-stirred reactor simulations."""

from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from .solve import Config

app = typer.Typer()


def read_temperatures(temps_file: Path) -> list[float]:
    """Load temperatures (K) from a CSV file with a 'temperature' column."""
    df = pl.read_csv(temps_file)
    return df.get_column(df.columns[0]).cast(pl.Float64).to_list()


def read_compositions(comps_file: Path) -> list[dict[str, float]]:
    """Load compositions from a YAML file with a 'compositions' key."""
    df = pl.read_csv(comps_file)
    return df.to_dicts()


@app.command()
def main(
    config_file: Annotated[
        str, typer.Argument(help="Path to YAML config file.")
    ] = "config.yaml",
    temps_file: Annotated[
        str | None,
        typer.Option(
            "--temps-file", "-t", help="Path to CSV file containing temperatures."
        ),
    ] = None,
    comps_file: Annotated[
        str | None,
        typer.Option(
            "--comps-file", "-c", help="Path to YAML file containing compositions."
        ),
    ] = None,
) -> None:
    """Run JSR simulations across multiple temperatures."""
    typer.echo(f"Loading config from: {config_file}")
    config = Config.read_yaml(Path(config_file))
    typer.echo(f"{config = }")

    if temps_file is not None:
        typer.echo(f"Loading temperatures from: {temps_file}")
        temperatures = read_temperatures(Path(temps_file))
        typer.echo(f"{temperatures = }")

    if comps_file is not None:
        typer.echo(f"Loading compositions from: {comps_file}")
        compositions = read_compositions(Path(comps_file))
        typer.echo(f"{compositions = }")
