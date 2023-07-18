from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class SSDApphook(CMSApp):
    app_name = "ssd"
    name = _("Benefits Application")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.cms.ssd.urls"]
        # return ["open_inwoner.profile.urls"]
