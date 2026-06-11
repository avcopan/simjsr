"""Configuration for simulations."""

from pathlib import Path
from typing import Any, Self

import polars as pl
import yaml
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration for a jet-stirred reactor simulation.

    Attributes:
        cantera_file: Cantera file (can be generated from Chemkin files)
        temperature: Temperature (K)
        pressure: Pressure (atm)
        residence_time: Residence time (s)
        volume: Reactor volume (cm^3)
        composition: Starting composition (mole fractions)
        time_out: Time limit for the simulation (s)
        chemkin_file: Chemkin mechanism file (used to generate Cantera file)
        chemkin_thermo_file: Chemkin thermo file (used to generate Cantera file)
    """

    cantera_file: Path = Field(
        description="Cantera file (can be generated from Chemkin files)"
    )
    temperature: float = Field(description="Temperature (K)")
    pressure: float = Field(description="Pressure (atm)")
    residence_time: float = Field(description="Residence time (s)")
    composition: dict[str, float] = Field(
        description="Starting composition (mole fractions)"
    )
    volume: float = Field(description="Reactor volume (cm^3)", default=1.0)
    time_out: float | None = Field(
        description="Time limit for the simulation (s)", default=None
    )
    chemkin_file: Path | None = Field(
        description="Chemkin mechanism file (used to generate Cantera file)",
        default=None,
    )
    chemkin_thermo_file: Path | None = Field(
        description="Chemkin thermo file (used to generate Cantera file)", default=None
    )

    def is_compatible_with(self, other: "Config | None") -> bool:
        """Check if this config is compatible with another config for chaining."""
        if other is None:
            return False
        return (
            self.cantera_file == other.cantera_file
            and self.composition == other.composition
        )

    def to_yaml(
        self,
        file: Path | str | None = None,
        *,
        update: dict[str, Any] | None = None,
        describe: bool = False,
    ) -> str:
        """Generate YAML text and (optionally) write to a file."""
        yaml_text = self.yaml_text(update=update, describe=describe)

        if file is not None:
            file = Path(file)
            file.write_text(yaml_text, encoding="utf-8")

        return yaml_text

    def yaml_text(
        self,
        *,
        update: dict[str, Any] | None = None,
        describe: bool = False,
    ) -> str:
        """Generate YAML text."""
        data = self.model_dump(mode="json")
        if update is not None:
            data.update(update)

        if not describe:
            return yaml.safe_dump(data, sort_keys=False)

        fields = []
        comments = []
        for field_name, field_info in Config.model_fields.items():
            field_value = _to_yaml_serialized_value(data[field_name])
            line = f"{field_name}: {field_value}"
            fields.append(line)
            comments.append(field_info.description)

        width = max(len(line) for line in fields)
        fields = [
            f"{line:<{width}}  # {comment}"
            for line, comment in zip(fields, comments, strict=True)
        ]
        return "\n".join(fields) + "\n"

    @classmethod
    def from_yaml(
        cls, *, file: str | Path | None = None, text: str | Path | None = None
    ) -> Self:
        """Instantiate from YAML file or text."""
        (config, *extra_configs), _ = cls.all_with_dataframe_from_yaml(
            file=file, text=text
        )
        if extra_configs:
            msg = f"Cannot read config from multi-config YAML. {extra_configs = }"
            raise ValueError(msg)
        return config

    @classmethod
    def all_with_dataframe_from_yaml(
        cls, *, file: str | Path | None = None, text: str | Path | None = None
    ) -> tuple[list[Self], pl.DataFrame | None]:
        """Instantiate  from YAML file or text and return as a DataFrame."""
        if file is not None:
            text = Path(file).read_text()

        if text is None:
            msg = "Either file or text must be provided."
            raise ValueError(msg)

        data = yaml.safe_load(text)
        temperature = data.get(Key.temperature)
        composition = data.get(Key.composition)

        if isinstance(temperature, str) and isinstance(composition, str):
            msg = f"{temperature = } and {composition = } cannot both be file paths."
            raise TypeError(msg)

        df = None
        datas = [data]
        if isinstance(temperature, str):
            df = pl.read_csv(temperature)
            datas = [{**data, Key.temperature: t} for t in df[:, 0]]

        if isinstance(composition, str):
            df = pl.read_csv(composition)
            datas = [{**data, Key.composition: c} for c in df.iter_rows(named=True)]

        configs = [cls.model_validate(d) for d in datas]
        return configs, df


class Key:
    """Keys for config fields."""

    temperature = "temperature"
    composition = "composition"


# Helpers
def _to_yaml_serialized_value(value: object) -> str:
    """Serialize a value to a YAML string."""
    return yaml.safe_dump(value, default_flow_style=True).splitlines()[0]
