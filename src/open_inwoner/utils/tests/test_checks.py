from django.core.checks import Warning
from django.test import TestCase

from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.mijn_afval.cms.cms_appconfig import MijnAfvalApphookConfig
from open_inwoner.utils.checks import check_apphook_configs


class CheckApphookConfigsTests(TestCase):
    def setUp(self):
        cms_tools.create_homepage()

    def test_no_warnings_when_page_namespace_matches_config(self):
        cms_tools.create_apphook_page(ProfileApphook)

        self.assertEqual(check_apphook_configs(None, databases=["default"]), [])

    def test_no_warnings_for_configs_of_apphooks_without_pages(self):
        # Mijn Afval's data migration creates a config without a page; that is not
        # a mismatch, as there is no page to apply it to
        self.assertTrue(MijnAfvalApphookConfig.objects.exists())

        self.assertEqual(check_apphook_configs(None, databases=["default"]), [])

    def test_warnings_when_page_namespace_matches_no_config(self):
        page = cms_tools.create_apphook_page(ProfileApphook)
        ProfileConfig.objects.filter(namespace=ProfileApphook.app_name).update(
            namespace="Mijn Profiel"
        )

        self.assertEqual(
            check_apphook_configs(None, databases=["default"]),
            [
                Warning(
                    f"CMS page {page.pk} uses apphook ProfileApphook with "
                    "application namespace 'profile', but no config has that "
                    "namespace. The page's views run without a config.",
                    hint=(
                        "Existing config namespaces: ['Mijn Profiel']. Select a "
                        "config in the page's advanced settings and save, or change "
                        "the namespace of a config to match the page."
                    ),
                    obj=page,
                    id="utils.W002",
                ),
                Warning(
                    "Config 'Mijn Profiel' for apphook ProfileApphook is not used by "
                    "any CMS page, so its settings have no effect.",
                    hint=(
                        "If a page should use this config, select it in that page's "
                        "advanced settings and save. Otherwise, delete the config."
                    ),
                    id="utils.W003",
                ),
            ],
        )
