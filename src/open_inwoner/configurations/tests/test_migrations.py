from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


def _text_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "link", "attrs": {"href": href}}],
                    }
                ],
            }
        ],
    }


@tag("migrations")
class SanitizeProsemirrorLinkHrefsMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0102: strip unsafe hrefs from stored prosemirror link marks
    on SiteConfiguration.warning_banner_text, login_text and search_zero_results_text.
    """

    migrate_from = "0101_alter_siteconfiguration_default_colors"
    migrate_to = "0102_sanitize_prosemirror_link_hrefs"
    app = "configurations"

    def setUpBeforeMigration(self, apps):
        SiteConfiguration = apps.get_model("configurations", "SiteConfiguration")

        self.config = SiteConfiguration.objects.create(name="Test")
        SiteConfiguration.objects.filter(pk=self.config.pk).update(
            warning_banner_text=_text_with_link("click", "javascript:alert(1)"),
            login_text=_text_with_link("click", "https://example.com"),
            search_zero_results_text=None,
        )

    def _get(self):
        SiteConfiguration = self.apps.get_model("configurations", "SiteConfiguration")
        return SiteConfiguration.objects.get(pk=self.config.pk)

    def test_unsafe_href_stripped_from_warning_banner_text(self):
        config = self._get()
        text_node = config.warning_banner_text.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])

    def test_safe_href_preserved_on_login_text(self):
        config = self._get()
        text_node = config.login_text.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"][0]["attrs"]["href"], "https://example.com")

    def test_empty_search_zero_results_text_is_untouched(self):
        config = self._get()
        self.assertIsNone(config.search_zero_results_text.raw_data)
