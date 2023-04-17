from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class CasesApphook(CMSApp):
    app_name = "cases"
    name = _("ZGW Application")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.cms.cases.urls"]
