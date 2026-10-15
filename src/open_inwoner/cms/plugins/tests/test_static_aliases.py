import json
import re
from unittest import mock

from django.conf import settings
from django.core import checks
from django.test import SimpleTestCase, TestCase

from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import BaseRenderer, StructureRenderer
from djangocms_alias.models import Alias, AliasContent, Category

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.cms.utils.static_aliases import (
    check_static_alias_plugin_restrictions,
    patch_static_alias_plugin_restrictions,
)


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


def incompatible_get_placeholder_toolbar_js(self, placeholder, page=None, extra=None):
    return ""


class StaticAliasPluginRestrictionPatchTests(SimpleTestCase):
    """
    If an upgrade of django-cms changes `BaseRenderer.get_placeholder_toolbar_js()`,
    the patch is skipped and a system check warns about it.
    """

    def run_check(self) -> list[checks.CheckMessage]:
        return check_static_alias_plugin_restrictions(app_configs=None)

    def test_patch_is_applied(self):
        self.assertEqual(self.run_check(), [])

    def test_patch_is_skipped_if_signature_changed(self):
        with mock.patch.object(
            BaseRenderer,
            "get_placeholder_toolbar_js",
            incompatible_get_placeholder_toolbar_js,
        ):
            patch_static_alias_plugin_restrictions()

            self.assertIs(
                BaseRenderer.get_placeholder_toolbar_js,
                incompatible_get_placeholder_toolbar_js,
            )
            self.assertEqual(
                self.run_check(),
                [
                    checks.Warning(
                        "The plugins of static aliases (the footer columns, the "
                        "login banner) are not restricted by their static code: "
                        "`BaseRenderer.get_placeholder_toolbar_js()` has the "
                        "signature `(self, placeholder, page=None, extra=None)`, "
                        "expected `(self, placeholder, page=None)`.",
                        hint=(
                            "Update `open_inwoner.cms.utils.static_aliases` for the "
                            "installed version of django-cms."
                        ),
                        obj=BaseRenderer,
                        id="open_inwoner.cms.W001",
                    )
                ],
            )

    def test_patch_is_skipped_if_method_was_removed(self):
        with mock.patch.object(BaseRenderer, "get_placeholder_toolbar_js", None):
            patch_static_alias_plugin_restrictions()

            self.assertIsNone(BaseRenderer.get_placeholder_toolbar_js)
            self.assertEqual(
                self.run_check(),
                [
                    checks.Warning(
                        "The plugins of static aliases (the footer columns, the "
                        "login banner) are not restricted by their static code: "
                        "`BaseRenderer.get_placeholder_toolbar_js()` does not exist.",
                        hint=(
                            "Update `open_inwoner.cms.utils.static_aliases` for the "
                            "installed version of django-cms."
                        ),
                        obj=BaseRenderer,
                        id="open_inwoner.cms.W001",
                    )
                ],
            )
