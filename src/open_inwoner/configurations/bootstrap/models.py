import dataclasses
from dataclasses import dataclass, field
from typing import Any, Iterator, TypeAlias

from django.contrib.postgres.fields import ArrayField
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ForeignKey, OneToOneField

from digid_eherkenning.models import DigidConfiguration

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import OpenZaakConfig

from .dataclasses import ConfigField, Fields

ConfigModel: TypeAlias = (
    SiteConfiguration
    | OpenKlantConfig
    | OpenZaakConfig
    | OpenIDConnectDigiDConfig
    | OpenIDConnectEHerkenningConfig
)


class ConfigSettingsBase:
    model: ConfigModel
    display_name: str
    namespace: str
    required_fields: tuple[str, ...]
    included_fields: tuple[str, ...]
    excluded_fields: tuple[str, ...]

    def __init__(self):
        self.config_fields = Fields(all=set(), required=set())

        self.create_model_config_fields(
            require=self.required_fields,
            exclude=self.excluded_fields,
            include=self.included_fields,
            model=self.model,
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
        if isinstance(field, (JSONField, ArrayField)):
            try:
                default = ", ".join(default)
            except TypeError:
                default = str(default)

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

    def get_model_fields(self, model) -> Iterator[Any]:
        return (
            field
            for field in model._meta.concrete_fields
            if field.name not in self.__class__.excluded_fields
        )

    def create_model_config_fields(
        self,
        require: tuple[str, ...],
        exclude: tuple[str, ...],
        include: tuple[str, ...],
        model: Any,
        relating_field: Any = None,
    ) -> None:

        model_fields = self.get_model_fields(model)

        for model_field in model_fields:
            if isinstance(model_field, (ForeignKey, OneToOneField)):
                self.create_model_config_fields(
                    require=require,
                    exclude=exclude,
                    include=include,
                    model=model_field.related_model,
                    relating_field=model_field,
                )
            else:
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
                # whitelist or blacklist
                if (
                    config_field.name in self.included_fields
                    or config_field not in self.excluded_fields
                ):
                    self.config_fields.all.add(config_field)
                if config_field.name in self.required_fields:
                    self.config_fields.required.add(config_field)

            # TODO: delegate image field, file field etc. to handler functions/classes

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
    required_fields = (
        "name",
        "primary_color",
        "secondary_color",
        "accent_color",
    )
    included_fields = ()
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
    required_fields = (
        "contactmomenten_service_client_id",
        "contactmomenten_service_secret",
        "contactmomenten_service_api_root",
        "klanten_service_client_id",
        "klanten_service_secret",
        "klanten_service_api_root",
        "register_type",
        "register_contact_moment",
    )
    included_fields = required_fields + (
        "register_bronorganisatie_rsin",
        "register_channel",
        "register_contact_moment",
        "register_email",
        "register_employee_id",
        "register_type",
        "use_rsin_for_innnnpid_query_parameter",
    )
    excluded_fields = ()


class ZGWConfigurationSettings(ConfigSettingsBase):
    model = OpenZaakConfig
    display_name = "ZGW Configuration"
    namespace = "ZGW_CONFIG"
    required_fields = (
        "catalogi_service_client_id",
        "catalogi_service_secret",
        "catalogi_service_api_root",
        "document_service_client_id",
        "document_service_secret",
        "document_service_api_root",
        "form_service_client_id",
        "form_service_secret",
        "form_service_api_root",
        "zaak_service_client_id",
        "zaak_service_secret",
        "zaak_service_api_root",
    )
    included_fields = required_fields + (
        "action_required_deadline_days",
        "allowed_file_extensions",
        "document_max_confidentiality",
        "enable_categories_filtering_with_zaken",
        "fetch_eherkenning_zaken_with_rsin",
        "max_upload_size",
        "reformat_esuite_zaak_identificatie",
        "skip_notification_statustype_informeren",
        "title_text",
        "zaak_max_confidentiality",
    )
    excluded_fields = ()


class DigiDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectDigiDConfig
    display_name = "DigiD OIDC Configuration"
    namespace = "DIGID_OIDC"
    api_fields = tuple()
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")
    included_fields = tuple()
    excluded_fields = ("id",)


class DigiDSAMLConfigurationSettings(ConfigSettingsBase):
    model = DigidConfiguration
    display_name = "DigiD SAML Configuration"
    namespace = "DIGID"
    api_fields = tuple()
    required_fields = (
        "certificate_label",
        "certificate_type",
        "certificate_public_certificate",
        "metadata_file_source",
        "entity_id",
        "base_url",
        "service_name",
        "service_description",
    )
    included_fields = ()
    excluded_fields = ("id",)


class eHerkenningDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectEHerkenningConfig
    display_name = "eHerkenning OIDC Configuration"
    namespace = "EHERKENNING_OIDC"
    api_fields = tuple()
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")
    included_fields = tuple()
    excluded_fields = ("id",)


@dataclass
class ConfigurationSettingsMap:
    siteconfig: type = field(default=SiteConfigurationSettings)
    kic: type = field(default=KICConfigurationSettings)
    zgw: type = field(default=ZGWConfigurationSettings)
    digid_saml: type = field(default=DigiDSAMLConfigurationSettings)
    digid_oidc: type = field(default=DigiDOIDCConfigurationSettings)
    eherkenning_oidc: type = field(default=eHerkenningDOIDCConfigurationSettings)

    # TODO: admin_oidc, eherkenning_saml

    @classmethod
    def get_fields(cls):
        return tuple(field.default for field in dataclasses.fields(cls))

    @classmethod
    def get_field_names(cls):
        return tuple(field.name for field in dataclasses.fields(cls))
