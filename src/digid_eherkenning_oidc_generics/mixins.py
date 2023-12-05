import logging

from mozilla_django_oidc_db.mixins import SoloConfigMixin as _SoloConfigMixin

from . import digid_settings, eherkenning_settings
from .models import OpenIDConnectDigiDConfig, OpenIDConnectEHerkenningConfig

logger = logging.getLogger(__name__)


class SoloConfigMixin(_SoloConfigMixin):
    config_class = ""
    settings_attribute = None

    def get_settings(self, attr, *args):
        if hasattr(self.settings_attribute, attr):
            return getattr(self.settings_attribute, attr)
        return super().get_settings(attr, *args)


class SoloConfigDigiDMixin(SoloConfigMixin):
    config_class = OpenIDConnectDigiDConfig
    settings_attribute = digid_settings


class SoloConfigEHerkenningMixin(SoloConfigMixin):
    config_class = OpenIDConnectEHerkenningConfig
    settings_attribute = eherkenning_settings
