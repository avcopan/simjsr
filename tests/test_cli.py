"""Test CLI."""

import contextlib
import shutil
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

import simjsr
from simjsr.cli import app

runner = CliRunner()

EXAMPLES = [
    (["example", "-f", "cantera"], "cantera_single", 1),
    (["example", "-f", "chemkin"], "chemkin_single", 1),
    (["example", "-f", "chemkin", "-t"], "chemkin_multi_temperature", 3),
    (["example", "-f", "chemkin", "-c"], "chemkin_multi_composition", 3),
]


def test__version_flag() -> None:
    """Test the long form --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"{simjsr.__version__}" in result.stdout


@pytest.mark.parametrize(("args", "name", "row_count"), EXAMPLES)
def test__examples(
    tmp_path: Path, examples_path: Path, args: list[str], name: str, row_count: int
) -> None:
    """Test example generation."""
    # 1. Remove the example directory if it exists
    example_dir = examples_path / name
    if example_dir.exists():
        shutil.rmtree(example_dir)

    # 2. Re-generate the example
    example_dir.mkdir()

    with contextlib.chdir(example_dir):
        runner.invoke(app, args, catch_exceptions=False)

    # 3. Copy to a temporary directory and run
    run_dir = tmp_path / name
    shutil.copytree(example_dir, run_dir)
    with contextlib.chdir(run_dir):
        runner.invoke(app, ["run"], catch_exceptions=False)

    # 4. Check the output file exists and has the expected number of rows
    output_file = run_dir / "output.csv"
    assert output_file.exists()
    assert pl.read_csv(output_file).height == row_count
