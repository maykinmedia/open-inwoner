from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from cms import api

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.core.cms.utils.cms_test_utils import render_full_page
from open_inwoner.utils.test import temp_media_root


@temp_media_root()
class CustomJavaScriptInclusionTests(TestCase):
    """Test that uploaded JavaScript is actually included in rendered pages"""

    def setUp(self):
        self.site_config = SiteConfiguration.get_solo()
        self.site_config.custom_javascript = None
        self.site_config.custom_javascript_confirmed = False
        self.site_config.save()

        self.page = api.create_page(
            title="Test Page",
            template="cms/fullwidth.html",
            language="nl",
            in_navigation=True,
        )
        self.page.publish("nl")
        self.js_content = 'console.log("Custom JS loaded");'
        self.js_file = SimpleUploadedFile(
            "test.js",
            self.js_content.encode("utf-8"),
            content_type="application/javascript",
        )

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_uploaded_javascript_included_in_head_when_enabled_and_confirmed(self):
        self.site_config.custom_javascript = self.js_file
        self.site_config.custom_javascript_confirmed = True
        self.site_config.save()

        rendered_html = render_full_page(self.page)

        expected_script_tag = f'<script nonce="test-nonce" src="{self.site_config.custom_javascript.url}" defer></script>'
        self.assertIn(expected_script_tag, rendered_html)

    @override_settings(ALLOW_CUSTOM_JS=False)
    def test_javascript_omitted_when_setting_is_disabled(self):
        for confirmed, js_file in zip((True, False), (self.js_file, None)):
            with self.subTest(f"{confirmed=} {js_file=}"):
                self.site_config.custom_javascript = js_file
                self.site_config.custom_javascript_confirmed = confirmed
                self.site_config.save()
                # Test the rendered page
                rendered_html = render_full_page(self.page)

                # Should not contain any script tag for custom JavaScript
                self.assertNotIn("custom_scripts", rendered_html)
                if self.site_config.custom_javascript:
                    self.assertNotIn(
                        self.site_config.custom_javascript.url, rendered_html
                    )

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_omitted_when_file_missing(self):
        self.site_config.custom_javascript = None
        self.site_config.save()

        rendered_html = render_full_page(self.page)

        self.assertNotIn("custom_scripts", rendered_html)

    @override_settings(ALLOW_CUSTOM_JS=True)
    def test_javascript_omitted_when_confirmation_missing(self):
        self.site_config.custom_javascript = self.js_file
        self.site_config.custom_javascript_confirmed = False
        self.site_config.save()

        rendered_html = render_full_page(self.page)

        self.assertNotIn("custom_scripts", rendered_html)
