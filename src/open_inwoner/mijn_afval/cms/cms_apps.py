from django.utils.translation import gettext_lazy as _

from aldryn_apphooks_config.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class MijnAfvalApphook(CMSApp):
    app_name = "mijn_afval"
    name = _("Mijn Afval")

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.mijn_afval.urls"]
