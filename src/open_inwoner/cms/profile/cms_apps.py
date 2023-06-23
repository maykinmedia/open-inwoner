from django.utils.translation import gettext_lazy as _

from aldryn_apphooks_config.app_base import CMSConfigApp
from cms.apphook_pool import apphook_pool

from .cms_appconfig import ProfileConfig


@apphook_pool.register
class ProfileApphook(CMSConfigApp):
    app_name = "profile"
    name = _("Profile Application")
    app_config = ProfileConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.cms.profile.urls"]
