"""Test simjsr.convert."""

from pathlib import Path

import cantera as ct
import pytest

from simjsr import convert


@pytest.mark.parametrize(
    argnames=("mech_file", "thermo_file", "species_count", "reaction_count"),
    argvalues=[
        ("grimech3.0/chem.inp", "grimech3.0/thermo.dat", 53, 325),
        ("grimech3.0/chem-all.inp", None, 53, 325),
    ],
)
def test__from_chemkin(  # noqa: PLR0913
    mech_file: str | Path,
    thermo_file: str | Path | None,
    species_count: int,
    reaction_count: int,
    data_path: Path,
    tmp_path: Path,
) -> None:
    """Stub test to ensure the test suite runs."""
    mech_file = data_path / mech_file
    thermo_file = None if thermo_file is None else data_path / thermo_file
    out_file = (tmp_path / mech_file.stem).with_suffix(".yaml")
    convert.from_chemkin(
        mech_file=mech_file, thermo_file=thermo_file, out_file=out_file
    )

    model = ct.Solution(out_file)
    assert model.n_species == species_count
    assert model.n_reactions == reaction_count
