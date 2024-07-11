from dataclasses import dataclass
from typing import Mapping, Sequence, Type

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.utils.module_loading import import_string

from .constants import basic_field_descriptions
from .exceptions import ImproperlyConfigured


@dataclass(frozen=True, slots=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    default_value: str
    field_description: str


class ConfigSettings:
    """
    Settings for configuration steps, also used to generate documentation.

    Attributes:
        enable_setting (`str`): the setting for enabling the associated configuration
            step
        namespace (`str`): the namespace of configuration variables for a given
            configuration
        file_name (`str`): the name of the file where the documentation is stored
        models (`list`): a list of models from which documentation is retrieved
        required_settings (`list`): required settings for a configuration step
        optional_settings (`list`): optional settings for a configuration step
        independent (`bool`): if `True` (the default), the documentation will be
            created in its own file; set to `False` if you want to avoid this and
            plan to embed the docs in another file (see `related_config_settings`)
        related_config_settings (`list`): optional list of `ConfigSettings` from
            related configuration steps; used for embedding documentation
        update_fields (`bool`): if `True`, custom model fields
            (along with their descriptions) are loaded via the settings variable
            `DJANGO_SETUP_CONFIG_CUSTOM_FIELDS`
        additional_info (`dict`): information for configuration settings which are
            not associated with a particular model field
        config_fields (`list`): a list of `ConfigField` objects containing information
            about Django model fields

    Example:
        Given a configuration step `FooConfigurationStep`: ::

        FooConfigurationStep(BaseConfigurationStep):
            verbose_name = "Configuration step for Foo"
            config_settings = ConfigSettings(
                enable_setting = "FOO_CONFIG_ENABLE"
                namespace="FOO",
                file_name="foo",
                models=["FooConfigurationModel"],
                required_settings=[
                    "FOO_SOME_SETTING",
                    "FOO_SOME_OTHER_SETTING",
                ],
                optional_settings=[
                    "FOO_SOME_OPT_SETTING",
                    "FOO_SOME_OTHER_OPT_SETTING",
                ],
                related_config_settings=[
                    "BarRelatedConfigurationStep.config_settings",
                ],
                additional_info={
                    "example_non_model_field": {
                        "variable": "FOO_EXAMPLE_NON_MODEL_FIELD",
                        "description": "Documentation for a field that cannot
                            be retrievend from a model",
                        "possible_values": "string (URL)",
                    },
                },
            )
    """

    def __init__(
        self,
        *args,
        enable_setting: str,
        namespace: str,
        file_name: str | None = None,
        models: list[Type[models.Model]] | None = None,
        required_settings: list[str],
        optional_settings: list[str] | None = None,
        independent: bool = True,
        related_config_settings: list["ConfigSettings"] | None = None,
        additional_info: dict[str, dict[str, str]] | None = None,
        update_fields: bool = False,
        **kwargs,
    ):
        self.enable_setting = enable_setting
        self.namespace = namespace
        self.file_name = file_name or self.namespace.lower()
        self.models = models
        self.required_settings = required_settings
        self.optional_settings = optional_settings or []
        self.independent = independent
        self.related_config_settings = related_config_settings or []
        self.additional_info = additional_info or {}
        self.update_fields = update_fields
        self.config_fields: list[ConfigField] = []

        if not self.models:
            return

        if update_fields:
            self.load_additional_fields()

        for model in self.models:
            self.create_config_fields(model=model)

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
    def load_additional_fields() -> None:
        """
        Add custom fields + descriptions defined in settings to
        `basic_field_descriptions`
        """
        custom_fields = getattr(settings, "DJANGO_SETUP_CONFIG_CUSTOM_FIELDS", None)
        if not custom_fields:
            return

        for mapping in custom_fields:
            try:
                field = import_string(mapping["field"])
            except ImportError as exc:
                raise ImproperlyConfigured(
                    "\n\nSomething went wrong when importing {field}.\n"
                    "Check your settings for django-setup-configuration".format(
                        field=mapping["field"]
                    )
                ) from exc
            else:
                description = mapping["description"]
                basic_field_descriptions[field] = description

    @staticmethod
    def get_field_description(field: models.Field) -> str:
        # fields with choices
        if choices := field.choices:
            example_values = [choice[0] for choice in choices]
            return ", ".join(example_values)

        # other fields
        field_type = type(field)
        if field_type in basic_field_descriptions.keys():
            return basic_field_descriptions.get(field_type, "")

        return "No information available"

    def create_config_fields(
        self,
        model: Type[models.Model],
        relating_field: models.Field | None = None,
    ) -> None:
        """
        Create a `ConfigField` instance for each field of the given `model` and
        add it to `self.fields`

        Basic fields (`CharField`, `IntegerField` etc) constitute the base case,
        relations (`ForeignKey`, `OneToOneField`) are handled recursively
        """

        for model_field in model._meta.fields:
            if isinstance(model_field, (ForeignKey, OneToOneField)):
                # avoid recursion error when following ForeignKey
                if model_field.name in ("parent", "owner"):
                    continue

                self.create_config_fields(
                    model=model_field.related_model,
                    relating_field=model_field,
                )
            else:
                # model field name could be "api_root",
                # but we need "xyz_service_api_root" (or similar) for consistency
                # when dealing with relations
                if relating_field:
                    config_field_name = f"{relating_field.name}_{model_field.name}"
                else:
                    config_field_name = model_field.name

                config_setting = self.get_config_variable(config_field_name)

                if not (
                    config_setting in self.required_settings
                    or config_setting in self.optional_settings
                ):
                    continue

                config_field = ConfigField(
                    name=config_field_name,
                    verbose_name=model_field.verbose_name,
                    description=model_field.help_text,
                    default_value=self.get_default_value(model_field),
                    field_description=self.get_field_description(model_field),
                )
                self.config_fields.append(config_field)

    #
    # convenience methods/properties for formatting
    #
    def get_config_variable(self, setting: str) -> str:
        return f"{self.namespace}_{setting.upper()}"
