"""Configuration for simulations."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class Config(BaseModel):
    """Configuration for a jet-stirred reactor simulation.

    Attributes:
        cantera_file: Cantera file path
        temperature: Temperature (K)
        pressure: Pressure (atm)
        residence_time: Residence time (s)
        volume: Volume (cm^3)
        composition: Starting composition (mole fractions)
        time_out: Time limit for the simulation (s)
    """

    cantera_file: Path
    temperature: float
    pressure: float
    residence_time: float
    composition: dict[str, float]
    volume: float = 1.0
    time_out: int | None = None

    model_config = {
        "json_schema_extra": {
            "field_meta": {
                "cantera_file": {"comment": "", "sample": "chem.yaml"},
                "temperature": {"comment": "K", "sample": 1000},
                "pressure": {"comment": "atm", "sample": 1},
                "residence_time": {"comment": "s", "sample": 4},
                "composition": {
                    "comment": "mole fractions",
                    "sample": {"CH4": 0.05, "O2": 0.21, "N2": 0.74},
                },
                "volume": {"comment": "cm^3", "sample": 1},
                "time_out": {"comment": "s", "sample": None},
            }
        }
    }

    def is_compatible_with(self, other: "Config | None") -> bool:
        """Check if this config is compatible with another config for chaining."""
        if other is None:
            return False
        return (
            self.cantera_file == other.cantera_file
            and self.composition == other.composition
        )

    def dump_yaml(self) -> str:
        """Dump the config to a YAML string."""
        data = self.model_dump(mode="json")
        return yaml.safe_dump(data, sort_keys=False)

    def write_yaml(self, path: Path) -> None:
        """Write the config to a YAML file."""
        path.write_text(self.dump_yaml(), encoding="utf-8")

    @classmethod
    def read_yaml(cls, path: Path) -> "Config":
        """Read the config from a YAML file."""
        return cls(**yaml.safe_load(Path(path).read_text()))

    @classmethod
    def sample_yaml(cls, write_path: Path | None = None) -> str:
        """Generate a sample YAML configuration."""
        field_meta: dict = cls.model_config["json_schema_extra"]["field_meta"]
        lines: list[str] = []

        for field_name in cls.model_fields:
            meta = field_meta[field_name]
            raw = yaml.safe_dump(
                {field_name: meta["sample"]},
            ).rstrip()

            if comment := meta["comment"]:
                first, *rest = raw.splitlines()
                raw = "\n".join([f"{first}  # {comment}", *rest])

            lines.append(raw)

        yaml_str = "\n".join(lines) + "\n"

        if write_path is not None:
            Path(write_path).write_text(yaml_str, encoding="utf-8")

        return yaml_str
