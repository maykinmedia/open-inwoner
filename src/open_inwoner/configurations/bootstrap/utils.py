from dataclasses import dataclass
from typing import Any, Iterator

from django.db.models.fields import NOT_PROVIDED


@dataclass(frozen=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    field_type: str
    default_value: str
    values: str


def populate_fields(
    fields: dict[str, list],
    require: tuple[str],
    exclude: tuple[str],
    all_fields: Iterator,
):
    for field in all_fields:
        config_field = ConfigField(
            name=field.name,
            verbose_name=field.verbose_name,
            description=field.description,
            field_type=field.get_internal_type(),
            default_value=get_default_value(field),
            values=get_example_value(field),
        )
        fields["all"].append(config_field)
        if require and config_field.name in require:
            fields["required"].append(config_field)


def get_default_value(field: Any) -> str:
    default = field.default

    if default is NOT_PROVIDED:
        return "No default"
    if not isinstance(default, (str, bool, int)):
        return "No information"

    return default


def get_example_value(field: Any) -> str:
    match field.get_internal_type():
        case "CharField":
            return "string"
        case "TextField":
            return "string"
        case "URLField":
            return "string (URL)"
        case "BooleanField":
            return "True, False"
        case "PositiveIntegerField":
            return "string representing a (positive) number"
        case "ArrayField":
            return "string, comma-delimited ('foo,bar,baz')"
        case _:
            return "No information available"


def generate_api_fields_from_template(api_name: str) -> dict[str, str]:
    name = api_name.split("_")[0].capitalize()

    return {
        f"{api_name}_root": {
            "verbose_name": f"Root URL of the {name} API",
            "values": "string (URL)",
        },
        f"{api_name}_client_id": {
            "verbose_name": f"Client ID for the {name} API",
            "values": "string",
        },
        f"{api_name}_client_secret": {
            "verbose_name": f"Secret for the {name} API",
            "values": "string",
        },
    }
