import json
import re

from django.conf import settings
from django.test import TestCase

from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import StructureRenderer
from djangocms_alias.models import Alias, AliasContent, Category

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools


class StaticAliasPluginRestrictionTests(TestCase):
    """
    The structure board offers the plugins configured for a static alias'
    static code in `CMS_PLACEHOLDER_CONF`, not those of the ``content`` slot all
    aliases share.
    """

    def setUp(self):
        super().setUp()
        cms_tools.create_static_aliases(["footer_left", "login_banner"])

        user = UserFactory(is_staff=True, is_superuser=True)
        self.renderer = StructureRenderer(request=cms_tools.get_request(user=user))

    def get_offered_plugins(self, alias_content: AliasContent) -> list[str]:
        toolbar_js = self.renderer.get_placeholder_toolbar_js(alias_content.placeholder)
        config = json.loads(re.search(r">(.*)</script>", toolbar_js).group(1))
        return sorted(config["plugin_restriction"])

    def get_expected_plugins(self, slot: str) -> list[str]:
        return sorted(
            settings.CMS_PLACEHOLDER_CONF[slot]["plugins"]
            + plugin_pool.get_system_plugins()
        )

    def test_footer_column_offers_the_footer_plugins(self):
        footer_left = AliasContent._base_manager.get(alias__static_code="footer_left")

        self.assertEqual(
            self.get_offered_plugins(footer_left),
            self.get_expected_plugins("footer_left"),
        )

    def test_login_banner_offers_the_banner_image_plugin(self):
        login_banner = AliasContent._base_manager.get(alias__static_code="login_banner")

        self.assertEqual(
            self.get_offered_plugins(login_banner),
            self.get_expected_plugins("login_banner"),
        )

    def test_alias_without_static_code_offers_the_content_plugins(self):
        alias = Alias.objects.create(category=Category.objects.create(name="Blokken"))
        alias_content = AliasContent._base_manager.create(
            alias=alias, name="Blok", language="nl"
        )

        self.assertEqual(
            self.get_offered_plugins(alias_content),
            self.get_expected_plugins("content"),
        )
