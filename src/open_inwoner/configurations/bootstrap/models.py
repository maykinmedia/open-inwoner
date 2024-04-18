from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.models import OpenZaakConfig

from .constants import (
    digid_oidc_fields,
    eherkenning_oidc_fields,
    kic_fields,
    siteconfig_fields,
    zgw_fields,
)
from .utils import ConfigField


class ConfigSettingsBase:
    @classmethod
    def get_setting_name(cls, field: ConfigField | str) -> str:
        if isinstance(field, str):
            return f"{cls.namespace}_" + field.upper()
        return f"{cls.namespace}_" + field.name.upper()

    @classmethod
    def get_required_settings(cls) -> list[str]:
        return [cls.get_setting_name(field) for field in cls.fields["required"]]

    @classmethod
    def get_config_mapping(cls) -> list[str]:
        return {cls.get_setting_name(field): field for field in cls.fields["all"]}


class SiteConfigurationSettings(ConfigSettingsBase):
    model = SiteConfiguration
    namespace = "SITE"
    fields = siteconfig_fields


class KICConfigurationSettings(ConfigSettingsBase):
    model = OpenKlantConfig
    namespace = "KIC_CONFIG"
    fields = kic_fields


class ZGWConfigurationSettings(ConfigSettingsBase):
    model = OpenZaakConfig
    namespace = "ZGW_CONFIG"
    fields = zgw_fields


class DigiDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectDigiDConfig
    namespace = "DIGID_OIDC"
    fields = digid_oidc_fields


class eHerkenningDOIDCConfigurationSettings(ConfigSettingsBase):
    model = OpenIDConnectEHerkenningConfig
    namespace = "EHERKENNING_OIDC"
    fields = eherkenning_oidc_fields
