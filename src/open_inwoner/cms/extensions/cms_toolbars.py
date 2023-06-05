from django.utils.translation import gettext_lazy as _

from cms.extensions.toolbar import ExtensionToolbar
from cms.toolbar_pool import toolbar_pool

from .models import CommonExtension


@toolbar_pool.register
class CommonExtensionToolbar(ExtensionToolbar):
    model = CommonExtension

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        if current_page_menu:
            page_extension, url = self.get_page_extension_admin()
            if url:
                current_page_menu.add_modal_item(
                    _("Pagina opties"),
                    url=url,
                    disabled=(not self.toolbar.edit_mode_active),
                    position=2,
                )
