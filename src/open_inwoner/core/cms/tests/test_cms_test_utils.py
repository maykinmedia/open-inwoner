from django.test import override_settings

from django_webtest import WebTest

from open_inwoner.core.cms.utils import cms_test_utils


@override_settings(ROOT_URLCONF="open_inwoner.core.cms.tests.urls")
class CMSToolsTests(WebTest):
    def test_create_homepage(self):
        p = cms_test_utils.create_homepage()
        response = self.app.get("/", status=200)
