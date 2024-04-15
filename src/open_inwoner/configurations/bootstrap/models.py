from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import OpenZaakConfig

from .constants import (
    catalogi_api_fields,
    contactmomenten_api_fields,
    digid_oidc_fields,
    documenten_api_fields,
    eherkenning_oidc_fields,
    formulieren_api_fields,
    kic_fields,
    klanten_api_fields,
    siteconfig_fields,
    zaak_api_fields,
    zgw_fields,
)


class ConfigSettingsBase:
    @classmethod
    def get_setting_name(cls, field_name):
        return f"{cls.namespace}_" + field_name.upper()

    @classmethod
    def get_required_settings(cls):
        return [cls.get_setting_name(field_name) for field_name in cls.required_fields]

    @classmethod
    def get_config_mapping(cls):
        return {cls.get_setting_name(field): field for field in cls.fields}


class SiteConfigurationSettings(ConfigSettingsBase):
    model = SiteConfiguration
    display_name = "Site"
    namespace = "SITE"
    required_fields = ("name", "primary_color", "secondary_color", "accent_color")
    fields = siteconfig_fields
    extra_fields = dict()


class KICConfigurationSettings(ConfigSettingsBase):
    model = OpenKlantConfig
    display_name = "Klanten configuration"
    namespace = "KIC_CONFIG"
    fields = kic_fields
    required_fields = (
        *klanten_api_fields.keys(),
        *contactmomenten_api_fields.keys(),
        "register_type",
        "register_contact_moment",
    )
    extra_fields = klanten_api_fields | contactmomenten_api_fields


class ZGWConfigurationSettings(ConfigSettingsBase):
    model = OpenZaakConfig
    display_name = "ZGW configuration"
    namespace = "ZGW_CONFIG"
    fields = zgw_fields
    required_fields = (
        *zaak_api_fields.keys(),
        *catalogi_api_fields.keys(),
        *documenten_api_fields.keys(),
        *formulieren_api_fields.keys(),
    )
    extra_fields = (
        zaak_api_fields
        | catalogi_api_fields
        | documenten_api_fields
        | formulieren_api_fields
    )


class DigiDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectDigiDConfig
    display_name = "DigiD OIDC authentication"
    namespace = "DIGID_OIDC"
    fields = digid_oidc_fields
    required_fields = ("oidp_rp_client_id", "oidp_rp_client_secret")
    extra_fields = dict()


class eHerkenningDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectEHerkenningConfig
    display_name = "eHerkenning OIDC authentication"
    namespace = "EHERKENNING_OIDC"
    fields = eherkenning_oidc_fields
    required_fields = ("eherkenning_rp_client_id", "eherkenning_rp_client_secret")
    extra_fields = dict()
