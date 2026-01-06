from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from aldryn_apphooks_config.utils import get_app_instance
from cms.extensions.toolbar import ExtensionToolbar
from cms.toolbar_pool import toolbar_pool

from .cms_appconfig import MijnAfvalApphookConfig
from .cms_apps import MijnAfvalApphook


@toolbar_pool.register
class MijnAfvalApphookConfigToolbar(ExtensionToolbar):
    model = MijnAfvalApphookConfig
    supported_apps = ("mijn_afval",)

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        if current_page_menu:
            self.namespace, self.config = get_app_instance(self.request)
            self.request.current_app = self.namespace

            if not self.config:
                url = reverse("admin:mijn_afval_cms_mijnafvalapphookconfig_changelist")
            else:
                url = reverse(
                    "admin:mijn_afval_cms_mijnafvalapphookconfig_change",
                    kwargs={"object_id": self.config.id},
                )

            current_page_menu.add_modal_item(
                _("Configuratie Mijn Afval"),
                url=url,
                disabled=(self.page.application_urls != MijnAfvalApphook.__name__),
            )
