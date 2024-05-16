from dataclasses import dataclass, field
from typing import Iterator, Mapping, Sequence

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ForeignKey, OneToOneField

from .choices import BasicFieldDescription


@dataclass(frozen=True, slots=True)
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


class ConfigSettingsBase:
    model: models.Model
    display_name: str
    namespace: str
    required_fields = tuple()
    all_fields = tuple()
    excluded_fields = ("id",)

    def __init__(self):
        self.config_fields = Fields()

        self.create_config_fields(
            require=self.required_fields,
            exclude=self.excluded_fields,
            include=self.all_fields,
            model=self.model,
        )

    @classmethod
    def get_setting_name(cls, field: ConfigField) -> str:
        return f"{cls.namespace}_" + field.name.upper()

    @staticmethod
    def get_default_value(field: models.Field) -> str:
        default = field.default

        if default is NOT_PROVIDED:
            return "No default"

        # needed to make `generate_config_docs` idempotent
        # because UUID's are randomly generated
        if isinstance(field, models.UUIDField):
            return "random UUID string"

        # if default is a function, call the function to retrieve the value;
        # we don't immediately return because we need to check the type first
        # and cast to another type if necessary (e.g. list is unhashable)
        if callable(default):
            default = default()

        if isinstance(default, Mapping):
            return str(default)

        # check for field type as well to avoid splitting values from CharField
        if isinstance(field, (JSONField, ArrayField)) and isinstance(default, Sequence):
            try:
                return ", ".join(str(item) for item in default)
            except TypeError:
                return str(default)

        return default

    @staticmethod
    def get_example_values(field: models.Field) -> str:
        # fields with choices
        if choices := field.choices:
            values = [choice[0] for choice in choices]
            return ", ".join(values)

        # other fields
        field_type = field.get_internal_type()
        match field_type:
            case item if item in BasicFieldDescription.names:
                return getattr(BasicFieldDescription, field_type)
            case _:
                return "No information available"

    def get_concrete_model_fields(self, model) -> Iterator[models.Field]:
        """
        Get all concrete fields for a given `model`, skipping over backreferences like
        `OneToOneRel` and fields that are blacklisted
        """
        return (
            field
            for field in model._meta.concrete_fields
            if field.name not in self.excluded_fields
        )

    def create_config_fields(
        self,
        require: tuple[str, ...],
        exclude: tuple[str, ...],
        include: tuple[str, ...],
        model: models.Model,
        relating_field: models.Field | None = None,
    ) -> None:
        """
        Create a `ConfigField` instance for each field of the given `model` and
        add it to `self.fields.all` and `self.fields.required`

        Basic fields (`CharField`, `IntegerField` etc) constitute the base case,
        relations (`ForeignKey`, `OneToOneField`) are handled recursively
        """

        model_fields = self.get_concrete_model_fields(model)

        for model_field in model_fields:
            if isinstance(model_field, (ForeignKey, OneToOneField)):
                self.create_config_fields(
                    require=require,
                    exclude=exclude,
                    include=include,
                    model=model_field.related_model,
                    relating_field=model_field,
                )
            else:
                if model_field.name in self.excluded_fields:
                    continue

                # model field name could be "api_root",
                # but we need "xyz_service_api_root" (or similar) for consistency
                if relating_field:
                    name = f"{relating_field.name}_{model_field.name}"
                else:
                    name = model_field.name

                config_field = ConfigField(
                    name=name,
                    verbose_name=model_field.verbose_name,
                    description=model_field.help_text,
                    default_value=self.get_default_value(model_field),
                    values=self.get_example_values(model_field),
                )

                if config_field.name in self.required_fields:
                    self.config_fields.required.add(config_field)

                # if all_fields is empty, that means we're filtering by blacklist,
                # hence the config_field is included by default
                if not self.all_fields or config_field.name in self.all_fields:
                    self.config_fields.all.add(config_field)

    def get_required_settings(self) -> tuple[str, ...]:
        return tuple(
            self.get_setting_name(field) for field in self.config_fields.required
        )

    def get_config_mapping(self) -> dict[str, ConfigField]:
        return {self.get_setting_name(field): field for field in self.config_fields.all}
