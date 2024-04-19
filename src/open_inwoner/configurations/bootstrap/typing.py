from typing import TypeAlias

from .models import (
    DigiDOIDCConfigurationSettings,
    KICConfigurationSettings,
    SiteConfigurationSettings,
    ZGWConfigurationSettings,
    eHerkenningDOIDCConfigurationSettings,
)

ConfigSetting: TypeAlias = (
    SiteConfigurationSettings
    | KICConfigurationSettings
    | ZGWConfigurationSettings
    | DigiDOIDCConfigurationSettings
    | eHerkenningDOIDCConfigurationSettings
)
