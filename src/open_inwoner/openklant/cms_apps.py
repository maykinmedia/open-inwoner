from django.utils.translation import gettext_lazy as _

from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool


@apphook_pool.register
class OpenklantApphook(CMSApp):
    app_name = "openklant"
    name = _("Openklant application")
    # the template new pages are created with: it declares the "contact_form"
    # placeholder rendered by `ContactFormView`
    page_template = "cms/contactform/form_outer.html"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["open_inwoner.openklant.urls"]
