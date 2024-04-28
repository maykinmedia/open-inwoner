from dataclasses import dataclass, field


@dataclass(frozen=True, eq=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    default_value: str
    values: str


@dataclass
class Fields:
    all: set[ConfigField] = field(default_factory=set)
    required: set[ConfigField] = field(default_factory=set)
