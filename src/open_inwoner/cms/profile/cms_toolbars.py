from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from cms.extensions.toolbar import ExtensionToolbar
from cms.toolbar_pool import toolbar_pool

from open_inwoner.cms.profile.cms_appconfig import ProfileConfig


@toolbar_pool.register
class ProfileApphookConfigToolbar(ExtensionToolbar):
    model = ProfileConfig

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        profile_config = ProfileConfig.objects.first()

        if not profile_config:
            url = reverse("admin:profile_profileconfig_changelist")
        else:
            url = reverse(
                "admin:profile_profileconfig_change",
                kwargs={"object_id": profile_config.id},
            )

        if current_page_menu:
            config_menu = current_page_menu.get_or_create_menu(
                "apphooks-configuration-menu", _("Apphook configurations"), position=4
            )
            config_menu.add_sideframe_item(_("Profile"), url=url)
