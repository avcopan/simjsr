"""Convert mechanism files to Cantera YAML format."""

from pathlib import Path

from cantera.ck2yaml import Parser


def from_chemkin(
    chemkin_file: str | Path,
    chemkin_thermo_file: str | Path | None = None,
    cantera_file: str | Path | None = None,
) -> str:
    """Convert Chemkin mechanism and thermo files to Cantera YAML format."""
    cantera_file = str(cantera_file or Path(chemkin_file).with_suffix(".yaml"))

    Parser.convert_mech(
        input_file=chemkin_file, thermo_file=chemkin_thermo_file, out_name=cantera_file
    )
    return str(cantera_file)
