from django.utils.translation import gettext_lazy as _

from aldryn_apphooks_config.app_base import CMSConfigApp
from cms.apphook_pool import apphook_pool

from .cms_appconfig import MijnAfvalApphookConfig


@apphook_pool.register
class MijnAfvalApphook(CMSConfigApp):
    app_name = "mijn_afval"
    name = _("Mijn Afval app")
    app_config = MijnAfvalApphookConfig

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.mijn_afval.urls"]
