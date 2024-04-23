from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    default_value: str
    values: str


@dataclass
class Fields:
    all: set[ConfigField]
    required: set[ConfigField]
