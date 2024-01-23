from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils.html import escape

from django_webtest import WebTest

from ...cms.tests import cms_tools
from ...utils.test import ClearCachesMixin, temp_media_root
from ..models import SiteConfiguration


@temp_media_root()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ThemestylesheetTest(ClearCachesMixin, WebTest):
    def test_theme_stylesheet_renders_tag(self):
        cms_tools.create_homepage()

        self.config = SiteConfiguration.get_solo()
        self.config.theme_stylesheet = ContentFile("text", "my_custom_theme.css")
        self.config.save()

        response = self.app.get(reverse("pages-root"))
        self.assertContains(response, self.config.theme_stylesheet.url)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ExtraCSSTest(ClearCachesMixin, WebTest):
    def test_extra_css_is_cleaned_on_save(self):
        self.config = SiteConfiguration.get_solo()
        self.config.extra_css = "body {color: red; unknown: bar; }"
        self.config.save()

        self.assertEquals("body {color: red; }", self.config.extra_css)

    def test_extra_css_rendered_in_homepage(self):
        cms_tools.create_homepage()

        self.config = SiteConfiguration.get_solo()
        self.config.extra_css = "body {color: red;}"
        self.config.save()

        response = self.app.get(reverse("pages-root"))
        extra_css = response.context.get("extra_css")

        expected = "body {color: red;}"
        actual = response.pyquery("#extra-css")[0].text.strip()
        self.assertEquals(expected, actual)

    def test_extra_css_rendered_in_homepage_is_escaped(self):
        cms_tools.create_homepage()

        self.config = SiteConfiguration.get_solo()
        css = 'body {color: "/style><script>evil();</script><style ";}'
        self.config.extra_css = css
        self.config.save()

        response = self.app.get(reverse("pages-root"))
        extra_css = response.context.get("extra_css")
        # not escaped in context
        self.assertEquals(extra_css, self.config.extra_css)

        style = response.pyquery("#extra-css")
        self.assertEqual(1, len(style))
        actual = style[0].text.strip()
        expected = escape(css)

        # escaped
        self.assertEquals(expected, actual)
