from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from aldryn_apphooks_config.utils import get_app_instance
from cms.extensions.toolbar import ExtensionToolbar
from cms.toolbar_pool import toolbar_pool

from open_inwoner.cms.profile.cms_appconfig import ProfileConfig


@toolbar_pool.register
class ProfileApphookConfigToolbar(ExtensionToolbar):
    model = ProfileConfig
    supported_apps = ("profile",)

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        self.namespace, self.config = get_app_instance(self.request)
        self.request.current_app = self.namespace

        if not self.config:
            url = reverse("admin:profile_profileconfig_changelist")
        else:
            url = reverse(
                "admin:profile_profileconfig_change",
                kwargs={"object_id": self.config.id},
            )

        current_page_menu.add_modal_item(
            _("Profile apphook configurations"),
            url=url,
            disabled=(not self.page.application_urls == "ProfileApphook"),
        )
