"""Test simjsr.convert."""

from pathlib import Path

import cantera as ct
import pytest

from simjsr import convert


@pytest.mark.parametrize(
    argnames=("cantera_file", "thermo_file", "species_count", "reaction_count"),
    argvalues=[
        ("grimech3.0/chem.inp", "grimech3.0/thermo.dat", 53, 325),
        ("grimech3.0/chem-all.inp", None, 53, 325),
    ],
)
def test__from_chemkin(  # noqa: PLR0913
    cantera_file: str | Path,
    thermo_file: str | Path | None,
    species_count: int,
    reaction_count: int,
    data_path: Path,
    tmp_path: Path,
) -> None:
    """Test conversion from Chemkin to Cantera format."""
    cantera_file = data_path / cantera_file
    thermo_file = None if thermo_file is None else data_path / thermo_file
    out_file = (tmp_path / cantera_file.stem).with_suffix(".yaml")
    convert.from_chemkin(
        chemkin_file=cantera_file,
        chemkin_thermo_file=thermo_file,
        cantera_file=out_file,
    )

    model = ct.Solution(out_file)
    assert model.n_species == species_count
    assert model.n_reactions == reaction_count
