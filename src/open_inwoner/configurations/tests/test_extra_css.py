from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from ...cms.tests import cms_tools
from ...utils.test import ClearCachesMixin
from ..models import SiteConfiguration


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ExtraCSSTest(ClearCachesMixin, WebTest):
    def setUp(self):
        cms_tools.create_homepage()

    def test_extra_css_rendered_in_homepage(self):
        self.config = SiteConfiguration.get_solo()
        self.config.extra_css = "body { .my-test-rule: my-test-value; }"
        self.config.save()

        response = self.app.get(reverse("pages-root"))
        extra_css = response.context.get("extra_css")

        self.assertEquals(extra_css, self.config.extra_css)
        self.assertContains(response, ".my-test-rule: my-test-value;")

    def test_extra_css_rendered_in_homepage_is_escaped(self):
        self.config = SiteConfiguration.get_solo()
        self.config.extra_css = "<script>evil();</script>"
        self.config.save()

        response = self.app.get(reverse("pages-root"))
        extra_css = response.context.get("extra_css")

        self.assertEquals(extra_css, self.config.extra_css)
        self.assertContains(response, "&lt;script&gt;evil();&lt;/script&gt;")
