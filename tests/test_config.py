"""Configuration for simulations."""

from pathlib import Path

from simjsr import Config


def test__to_yaml(grimech_config: Config, tmp_path: Path) -> None:
    """Test the roundtrip functionality."""
    out_file = tmp_path / "config.yaml"
    grimech_config.to_yaml(out_file)
    config = Config.from_yaml(file=out_file)
    assert config == grimech_config


def test__to_yaml_with_description(grimech_config: Config, tmp_path: Path) -> None:
    """Test the roundtrip functionality."""
    out_file = tmp_path / "config.yaml"
    grimech_config.to_yaml(out_file, describe=True)
    config = Config.from_yaml(file=out_file)
    assert config == grimech_config


def test__multi_from_yaml_single(grimech_config_single_path: Path) -> None:
    """Test loading a single config."""
    configs, _ = Config.all_with_dataframe_from_yaml(file=grimech_config_single_path)
    assert len(configs) == 1
