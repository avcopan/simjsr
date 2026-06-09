"""Convert mechanism files to Cantera YAML format."""

from pathlib import Path

from cantera.ck2yaml import Parser


def from_chemkin(
    mech_file: str | Path,
    thermo_file: str | Path | None = None,
    out_file: str | Path | None = None,
) -> str:
    """Convert Chemkin mechanism and thermo files to Cantera YAML format."""
    out_file = str(out_file or Path(mech_file).with_suffix(".yaml"))

    Parser.convert_mech(
        input_file=mech_file, thermo_file=thermo_file, out_name=out_file
    )
    return str(out_file)
