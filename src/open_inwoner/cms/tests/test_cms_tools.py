from django.test import override_settings

from django_webtest import WebTest

from open_inwoner.cms.tests import cms_tools


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CMSToolsTests(WebTest):
    def test_create_homepage(self):
        p = cms_tools.create_homepage()
        response = self.app.get("/", status=200)
