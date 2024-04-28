import dataclasses
from dataclasses import dataclass
from typing import Iterator, TypeAlias

from django.contrib.postgres.fields import ArrayField
from django.db import models
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

from .choices import BasicFieldDescription
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
    required_fields = tuple()
    included_fields = tuple()
    excluded_fields = ("id",)

    def __init__(self):
        self.config_fields = Fields()

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
    def get_default_value(field: models.Field) -> str:
        default = field.default

        if default is NOT_PROVIDED:
            return "No default"
        if callable(default):
            default = default()
        if isinstance(field, (JSONField, ArrayField)):
            try:
                default = ", ".join(default)
            except TypeError:
                default = str(default)
        # needed to make `generate_config_docs` idempotent
        # because UUID's are randomly generated
        if isinstance(field, models.UUIDField):
            default = "random UUID string"

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

    def get_model_fields(self, model) -> Iterator[models.Field]:
        return (
            field
            for field in model._meta.concrete_fields
            if field.name not in self.excluded_fields
        )

    def create_model_config_fields(
        self,
        require: tuple[str, ...],
        exclude: tuple[str, ...],
        include: tuple[str, ...],
        model: models.Field,
        relating_field: models.Field = None,
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

                if config_field.name in self.required_fields:
                    self.config_fields.required.add(config_field)

                # use combination of whitelist/blacklist for all fields
                if self.included_fields:
                    if (
                        config_field.name in self.included_fields
                        and config_field not in self.excluded_fields
                    ):
                        self.config_fields.all.add(config_field)
                elif config_field.name not in self.excluded_fields:
                    self.config_fields.all.add(config_field)

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
        "use_rsin_for_innNnpId_query_parameter",
    )
    excluded_fields = (
        "contactmomenten_service_uuid",
        "klanten_service_uuid",
    )


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


class DigiDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectDigiDConfig
    display_name = "DigiD OIDC Configuration"
    namespace = "DIGID_OIDC"
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")
    included_fields = tuple()


class DigiDSAMLConfigurationSettings(ConfigSettingsBase):
    model = DigidConfiguration
    display_name = "DigiD SAML Configuration"
    namespace = "DIGID"
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


class eHerkenningDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectEHerkenningConfig
    display_name = "eHerkenning OIDC Configuration"
    namespace = "EHERKENNING_OIDC"
    required_fields = ("oidc_rp_client_id", "oidc_rp_client_secret")


@dataclass
class ConfigurationSettingsMap:
    siteconfig: ConfigModel = SiteConfigurationSettings
    kic: ConfigModel = KICConfigurationSettings
    zgw: ConfigModel = ZGWConfigurationSettings
    digid_oidc: ConfigModel = DigiDOIDCConfigurationSettings
    digid_saml: ConfigModel = DigiDSAMLConfigurationSettings
    eherkenning_oidc: ConfigModel = eHerkenningDOIDCConfigurationSettings

    @classmethod
    def get_fields(cls):
        return tuple(getattr(cls, field.name) for field in dataclasses.fields(cls))

    @classmethod
    def get_field_names(cls):
        return tuple(field.name for field in dataclasses.fields(cls))
