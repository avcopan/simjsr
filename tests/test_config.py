"""Configuration for simulations."""

from pathlib import Path

from simjsr import Config


def test__roundtrip(grimech_config: Config, tmp_path: Path) -> None:
    """Test the roundtrip functionality."""
    out_file = tmp_path / "config.yaml"
    grimech_config.write_yaml(out_file)
    config = Config.read_yaml(out_file)
    assert config == grimech_config


def test__sample_yaml(tmp_path: Path) -> None:
    """Test the sample YAML generation."""
    out_file = tmp_path / "sample_config.yaml"
    Config.sample_yaml(out_file)
    config = Config.read_yaml(out_file)
    assert config == Config(
        mech_file=Path("chem.yaml"),
        temperature=1000,
        pressure=1,
        residence_time=4,
        composition={"CH4": 0.05, "O2": 0.21, "N2": 0.74},
        volume=1.0,
        time_out=None,
    )
