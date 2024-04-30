import dataclasses
from typing import TypeAlias

from .auth import (
    AdminOIDCConfigurationSettings,
    DigiDOIDCConfigurationSettings,
    DigiDSAMLConfigurationSettings,
    eHerkenningOIDCConfigurationSettings,
    eHerkenningSAMLConfigurationSettings,
)
from .kic import KICConfigurationSettings
from .siteconfig import SiteConfigurationSettings
from .zgw import ZGWConfigurationSettings

ConfigSetting: TypeAlias = (
    SiteConfigurationSettings
    | KICConfigurationSettings
    | ZGWConfigurationSettings
    | AdminOIDCConfigurationSettings
    | DigiDOIDCConfigurationSettings
    | DigiDSAMLConfigurationSettings
    | eHerkenningOIDCConfigurationSettings
    | eHerkenningSAMLConfigurationSettings
)


@dataclasses.dataclass
class ConfigurationRegistry:
    siteconfig: ConfigSetting = SiteConfigurationSettings
    kic: ConfigSetting = KICConfigurationSettings
    zgw: ConfigSetting = ZGWConfigurationSettings
    admin_oidc: ConfigSetting = AdminOIDCConfigurationSettings
    digid_oidc: ConfigSetting = DigiDOIDCConfigurationSettings
    digid_saml: ConfigSetting = DigiDSAMLConfigurationSettings
    eherkenning_oidc: ConfigSetting = eHerkenningOIDCConfigurationSettings
    eherkenning_saml: ConfigSetting = eHerkenningSAMLConfigurationSettings

    @classmethod
    def get_fields(cls):
        return tuple(getattr(cls, field.name) for field in dataclasses.fields(cls))

    @classmethod
    def get_field_names(cls):
        return tuple(field.name for field in dataclasses.fields(cls))
