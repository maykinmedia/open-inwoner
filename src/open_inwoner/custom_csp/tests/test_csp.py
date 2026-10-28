from django.conf import settings
from django.test import override_settings

from django_webtest import WebTest
from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory


@override_settings(
    CONTENT_SECURITY_POLICY=settings.CONTENT_SECURITY_POLICY
    or settings.CONTENT_SECURITY_POLICY_REPORT_ONLY,
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
)
class SkipStaffCSPMiddlewareTest(WebTest):
    def test_csp_active_for_anonynous(self):
        response = self.app.get("/")
        self.assertIn("Content-Security-Policy", response.headers)

    def test_csp_active_for_digid_login(self):
        user = DigidUserFactory()
        response = self.app.get("/", user=user)
        self.assertIn("Content-Security-Policy", response.headers)

    def test_csp_disabled_for_staff_login(self):
        user = UserFactory(is_staff=True)
        response = self.app.get("/", user=user)
        self.assertNotIn("Content-Security-Policy", response.headers)

    def test_csp_disabled_for_staff_login_admin(self):
        user = UserFactory(is_staff=True)
        response = self.app.get("/admin", user=user)
        self.assertNotIn("Content-Security-Policy", response.headers)


@override_settings(
    CONTENT_SECURITY_POLICY=settings.CONTENT_SECURITY_POLICY
    or settings.CONTENT_SECURITY_POLICY_REPORT_ONLY,
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
    # the cache is not reset between tests, nor invalidated by their rollback
    MKN_CSP_CACHE_TIMEOUT=0,
)
class DatabaseDirectivesTest(WebTest):
    def test_csp_includes_database_directives(self):
        CSPSetting.objects.create(
            directive=CSPDirective.IMG_SRC, value="https://example.com"
        )

        response = self.app.get("/")

        self.assertIn(
            "https://example.com", response.headers["Content-Security-Policy"]
        )
