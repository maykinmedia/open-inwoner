from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool

from .cms_appconfig import ProfileConfig


@apphook_pool.register
class ProfileApphook(CMSApp):
    app_name = "profile"
    name = _("Profile Application")
    app_config = ProfileConfig

    def get_config(self, namespace):
        return ProfileConfig.objects.filter(namespace=namespace).first()

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.cms.profile.urls"]
