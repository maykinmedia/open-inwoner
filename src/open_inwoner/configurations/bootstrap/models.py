import dataclasses
from dataclasses import dataclass, field
from typing import Any, Iterator, TypeAlias

from django.db.models.fields import NOT_PROVIDED

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import OpenZaakConfig

ConfigModel: TypeAlias = (
    SiteConfiguration
    | OpenKlantConfig
    | OpenZaakConfig
    | OpenIDConnectDigiDConfig
    | OpenIDConnectEHerkenningConfig
)


@dataclass(frozen=True)
class ConfigField:
    name: str
    verbose_name: str
    description: str
    default_value: str
    values: str


@dataclass
class Fields:
    all: list[ConfigField]
    required: list[ConfigField]


class ConfigSettingsBase:
    model: ConfigModel
    display_name: str
    namespace: str
    api_fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    excluded_fields: tuple[str, ...]
    api_fields: tuple[str, ...]

    def __init__(self):
        self.config_fields = Fields(all=[], required=[])

        self.populate_fields(
            required=self.required_fields,
            excluded=self.excluded_fields,
            model_fields=self.create_model_config_fields(),
            api_fields=self.create_api_config_fields(),
        )

    @classmethod
    def get_setting_name(cls, field: ConfigField) -> str:
        return f"{cls.namespace}_" + field.name.upper()

    @staticmethod
    def get_default_value(field: Any) -> str:
        default = field.default

        if default is NOT_PROVIDED:
            return "No default"
        if callable(default):
            default = default.__call__()

        return default

    @staticmethod
    def get_example_values(field: Any) -> str:
        # fields with choices
        if choices := field.choices:
            values = [choice[0] for choice in choices]
            return ", ".join(values)

        # other fields
        match field.get_internal_type():
            case "CharField":
                return "string"
            case "TextField":
                return "string"
            case "URLField":
                return "string (URL)"
            case "BooleanField":
                return "True, False"
            case "IntegerField":
                return "string representing a number"
            case "PositiveIntegerField":
                return "string representing a positive number"
            case "ArrayField":
                return "string, comma-delimited ('foo,bar,baz')"
            case _:
                return "No information available"

    def create_model_config_fields(self) -> Iterator[ConfigField]:
        model_fields = (
            field
            for field in self.model._meta.concrete_fields
            if field.name not in self.__class__.excluded_fields
        )

        return (
            ConfigField(
                name=model_field.name,
                verbose_name=model_field.verbose_name,
                description=model_field.help_text,
                default_value=self.get_default_value(model_field),
                values=self.get_example_values(model_field),
            )
            for model_field in model_fields
        )

    def create_single_api_config_field(self, api_field: str) -> ConfigField:
        api_type = api_field.split("_api_")[0].capitalize()

        if "api_root" in api_field:
            verbose_name = f"Root URL of the {api_type} API"
            values = "string (URL)"
        elif "api_client_id" in api_field:
            verbose_name = f"Client ID of the {api_type} API"
            values = "string"
        else:
            verbose_name = f"Client Secret of the {api_type} API"
            values = "string"

        return ConfigField(
            name=api_field,
            verbose_name=verbose_name,
            description="No description",
            default_value="No default",
            values=values,
        )

    def create_api_config_fields(self) -> Iterator[ConfigField]:
        return (
            self.create_single_api_config_field(field_name)
            for field_name in self.api_fields
        )

    def populate_fields(
        self,
        required: tuple[str, ...],
        excluded: tuple[str, ...],
        model_fields: Iterator[ConfigField],
        api_fields: Iterator[ConfigField],
    ) -> None:
        for config_field in model_fields:
            self.config_fields.all.append(config_field)
            if config_field.name in self.required_fields:
                self.config_fields.required.append(config_field)

        for config_field in api_fields:
            self.config_fields.all.append(config_field)
            self.config_fields.required.append(config_field)

    def get_required_settings(self) -> tuple[str, ...]:
        return tuple(
            self.get_setting_name(field) for field in self.config_fields.required
        )

    def get_config_mapping(self) -> dict[str, ConfigField]:
        return {self.get_setting_name(field): field for field in self.config_fields.all}


class SiteConfigurationSettings(ConfigSettingsBase):
    model = SiteConfiguration
    display_name = "General Configuration"
    namespace = "SITE"
    api_fields = tuple()
    required_fields = (
        "name",
        "primary_color",
        "secondary_color",
        "accent_color",
    )
    excluded_fields = (
        "id",
        "email_logo",
        "footer_logo",
        "favicon",
        "openid_connect_logo",
        "extra_css",
        "logo",
        "hero_image_login",
        "theme_stylesheet",
    )


class KICConfigurationSettings(ConfigSettingsBase):
    model = OpenKlantConfig
    display_name = "Klanten Configuration"
    namespace = "KIC_CONFIG"
    api_fields = (
        "contactmomenten_api_client_id",
        "contactmomenten_api_client_secret",
        "contactmomenten_api_root",
        "klanten_api_client_id",
        "klanten_api_client_secret",
        "klanten_api_root",
    )
    required_fields = api_fields + (
        "register_type",
        "register_contact_moment",
    )
    excluded_fields = ("id", "klanten_service", "contactmomenten_service")


class ZGWConfigurationSettings(ConfigSettingsBase):
    model = OpenZaakConfig
    display_name = "ZGW Configuration"
    namespace = "ZGW_CONFIG"
    api_fields = (
        "catalogi_api_client_id",
        "catalogi_api_client_secret",
        "catalogi_api_root",
        "documenten_api_client_id",
        "documenten_api_client_secret",
        "documenten_api_root",
        "formulieren_api_client_id",
        "formulieren_api_client_secret",
        "formulieren_api_root",
        "zaak_api_client_id",
        "zaak_api_client_secret",
        "zaak_api_root",
    )
    required_fields = api_fields
    excluded_fields = (
        "id",
        "catalogi_service",
        "document_service",
        "form_service",
        "zaak_service",
    )


class DigiDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectDigiDConfig
    display_name = "DigiD OIDC Configuration"
    namespace = "DIGID_OIDC"
    api_fields = tuple()
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")
    excluded_fields = ("id",)


class eHerkenningDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectEHerkenningConfig
    display_name = "eHerkenning OIDC Configuration"
    namespace = "EHERKENNING_OIDC"
    api_fields = tuple()
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")
    excluded_fields = ("id",)


@dataclass
class ConfigurationSettingsMap:
    siteconfig: type = field(default=SiteConfigurationSettings)
    kic: type = field(default=KICConfigurationSettings)
    zgw: type = field(default=ZGWConfigurationSettings)
    digid_oidc: type = field(default=DigiDOIDCConfigurationSettings)
    eherkenning_oidc: type = field(default=eHerkenningDOIDCConfigurationSettings)

    @classmethod
    def get_fields(cls):
        return tuple(field.default for field in dataclasses.fields(cls))

    @classmethod
    def get_field_names(cls):
        return tuple(field.name for field in dataclasses.fields(cls))
