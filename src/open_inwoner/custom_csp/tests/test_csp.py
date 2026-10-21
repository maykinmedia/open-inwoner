from django.conf import settings
from django.test import override_settings

from django_webtest import WebTest

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
